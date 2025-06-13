// === Configuration & Paths ===
const fs = require('fs');
const path = require('path');
const os = require('os');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const PQueue = require('p-queue').default;
const csv = require('csv-parser');
puppeteer.use(StealthPlugin());
const tmp = require('os').tmpdir();
const MAPS_DIR = path.join(__dirname, 'outputMadridMunicipalities');
const LINKS_FOLDER = path.join(MAPS_DIR, 'links');
const GRID_FILE = 'grid_output_municipalities.json';
const COMBINED_URLS_FILE = 'combined_urls.json';
const PROGRESS_FILE = path.join(MAPS_DIR, 'progress.json');
const SEEN_IDS_FILE = path.join(MAPS_DIR, 'seen_place_ids.json');
const NEW_LINKS_FILE = path.join(MAPS_DIR, 'new_links.json');
const STATS_CSV_FILE = path.join(MAPS_DIR, 'stats.csv');
const ERROR_CSV_FILE = path.join(MAPS_DIR, 'error.csv');
const COPIES_CSV_FILE = path.join(MAPS_DIR, 'copies.csv');
const GRID_SUMMARY_CSV = path.join(MAPS_DIR, 'grid_summary.csv');
const CATEGORY_SUMMARY_CSV = path.join(MAPS_DIR, 'category_summary.csv');
const REMOVED_CATEGORIES_FILE = path.join(MAPS_DIR, 'removed_categories.csv');
const NO_LINKS_CSV_FILE = path.join(MAPS_DIR, 'no_links.csv');
const BLOOM_FILE = path.join(MAPS_DIR, 'seen_placeids.bloom.json');
const FUNCTION_TIMES_CSV = path.join(MAPS_DIR, 'function_timings.csv');
const SYSTEM_STATS_FILE = path.join(MAPS_DIR, 'system_resource_log.txt');
const { BloomFilter } = require('bloom-filters');
const RESTART_AFTER_JOBS = 100; // Change this value as needed
let jobsSinceRestart = 0;
let newLinksSinceRestart = 0;
const RESTART_LOG_CSV = path.join(MAPS_DIR, 'restart_log.csv');
const FALSE_POSITIVE_LOG_FILE = path.join(MAPS_DIR, 'bloom_false_positives.log');

// === Timing Helpers ===
// Create directory for timings file
function ensureDirExists(filePath) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

// Create dirs for time logging
ensureDirExists(FUNCTION_TIMES_CSV);
ensureDirExists(SYSTEM_STATS_FILE);
ensureDirExists(FALSE_POSITIVE_LOG_FILE);

// Initialize the function timings CSV file if it doesn't exist
if (!fs.existsSync(FUNCTION_TIMES_CSV)) {
  fs.writeFileSync(FUNCTION_TIMES_CSV, 'timestamp,grid,layer,function,time_ms\n');
}

// Initialize false positive log if it doesn't exist
if (!fs.existsSync(FALSE_POSITIVE_LOG_FILE)) {
  fs.writeFileSync(FALSE_POSITIVE_LOG_FILE, 'timestamp,grid,layer,place_id,status\n');
}

// Async function execution timer
async function logExecutionTime(fn, fnName, grid, layer, ...args) {
  const start = Date.now();
  const result = await fn(...args);
  const duration = Date.now() - start;
  // Defensive: flatten grid and layer as string
  const gridName = typeof grid === 'string' ? grid : (grid?.name || '');
  const layerStr = typeof layer === 'string' ? layer : (layer || '');
  const line = `${new Date().toISOString()},${gridName},${layerStr},${fnName},${duration}\n`;
  fs.appendFileSync(FUNCTION_TIMES_CSV, line);
  return result;
}

// Sync function execution timer
function logExecutionTimeSync(fn, fnName, grid, layer, ...args) {
  const start = Date.now();
  const result = fn(...args);
  const duration = Date.now() - start;
  // Defensive: flatten grid and layer as string
  const gridName = typeof grid === 'string' ? grid : (grid?.name || '');
  const layerStr = typeof layer === 'string' ? layer : (layer || '');
  const line = `${new Date().toISOString()},${gridName},${layerStr},${fnName},${duration}\n`;
  fs.appendFileSync(FUNCTION_TIMES_CSV, line);
  return result;
}

// Log system statistics
function logSystemStats() {
  const now = new Date().toISOString();
  const mem = process.memoryUsage();
  const cpu = os.loadavg();
  const stats = [
    `Time: ${now}`,
    `RSS: ${mem.rss}`,
    `Heap Total: ${mem.heapTotal}`,
    `Heap Used: ${mem.heapUsed}`,
    `External: ${mem.external}`,
    `Array Buffers: ${mem.arrayBuffers}`,
    `CPU 1min: ${cpu[0]}`,
    `CPU 5min: ${cpu[1]}`,
    `CPU 15min: ${cpu[2]}`,
    `Free Mem: ${os.freemem()}`,
    `Total Mem: ${os.totalmem()}`,
    `-----------------------`
  ].join('\n');
  fs.appendFileSync(SYSTEM_STATS_FILE, stats + '\n');
}
logSystemStats();
setInterval(logSystemStats, 30 * 60 * 1000);

// === Rest of Config ===
const protectedFiles = ['cat.csv', 'grid_output_all.json'];
const writeProtect = (filePath) => {
  if (protectedFiles.some(f => filePath.endsWith(f))) {
    throw new Error(`Write attempt blocked: ${filePath} is read-only.`);
  }
};
let browser = null;
let tabs = [];
const LAYER1_THRESHOLD = 40;
const LAYER2_THRESHOLD = 60;
const L2_NO_UNIQUE_LIMIT = 2;
const L3_NO_UNIQUE_LIMIT = 16; 
const NUM_WORKERS = 20;
const HEADLESS = true;
const L2_CONSECUTIVE_FULL_REPEATS_LIMIT = 3;
const l2ConsecutiveFullRepeats = {};
const NAVIGATION_TIMEOUT = 60000;
const SKIP_LAYER2 = false;     // set true to go directly from L1 → L3
const RUN_L2_ONLY = false;     // for debugging L2 only
const RUN_L3_ONLY = true;     // for debugging L3 only
const PUPPETEER_PROFILE_DIR = path.join(tmp, 'puppeteer-temp-profile'); // 🧼 custom profile dir
const BLOOM_EXPECTED_ITEMS = 1000000; // Increased from 200,000 to reduce false positives
const BLOOM_ERROR_RATE = 0.0001; // Decreased from 0.001 to reduce false positives
const ENABLE_SECONDARY_VERIFICATION = true; // Set to true to enable backup verification method

// Secondary verification - Exact Place ID Tracking
const exactPlaceIds = new Set(); // For secondary verification of bloom filter

// === Helper Functions with Timing ===
function getElapsedMinutes(ms) {
  return (ms / 60000).toFixed(2);
}

function logRestartStats() {
  ensureDirExists(RESTART_LOG_CSV);
  const header = 'timestamp,jobs_since_restart,new_links_since_restart\n';
  const line = `${new Date().toISOString()},${jobsSinceRestart},${newLinksSinceRestart}\n`;
  if (!fs.existsSync(RESTART_LOG_CSV)) {
    fs.writeFileSync(RESTART_LOG_CSV, header + line);
  } else {
    fs.appendFileSync(RESTART_LOG_CSV, line);
  }
}

function logFalsePositive(placeId, gridName, level, status) {
  const timestamp = new Date().toISOString();
  const line = `${timestamp},${gridName},${level},${placeId},${status}\n`;
  fs.appendFileSync(FALSE_POSITIVE_LOG_FILE, line);
}

function restartProcess() {
  logRestartStats();
  console.log(`♻️ Restarting process after ${RESTART_AFTER_JOBS} jobs...`);
  process.exit(100); // Use a custom exit code for planned restart
}
// Wrap sync utility functions with timing
function getPlaceId(url, gridName = '', level = '') {
  return logExecutionTimeSync(_getPlaceIdInner, 'getPlaceId', gridName, level, url);
}

function _getPlaceIdInner(url) {
  if (!url || typeof url !== 'string') return null;
  const match16 = url.match(/!16s([^!&]+)/);
  if (match16) return decodeURIComponent(match16[1]);
  const match1 = url.match(/!1s([^!&]+)/);
  return match1 ? match1[1] : null;
}

function extractCoordsFromUrl(url, gridName = '', level = '') {
  return logExecutionTimeSync(_extractCoordsFromUrlInner, 'extractCoordsFromUrl', gridName, level, url);
}

function _extractCoordsFromUrlInner(url) {
  if (!url || typeof url !== 'string') return null;
  const match = url.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
  return match ? [parseFloat(match[1]), parseFloat(match[2])] : null;
}

function isInsideBoundingBox(lat, lng, minLat, maxLat, minLng, maxLng, gridName = '', level = '') {
  return logExecutionTimeSync(
    _isInsideBoundingBoxInner, 
    'isInsideBoundingBox', 
    gridName, 
    level, 
    lat, lng, minLat, maxLat, minLng, maxLng
  );
}

function _isInsideBoundingBoxInner(lat, lng, minLat, maxLat, minLng, maxLng) {
  return lat >= minLat && lat <= maxLat && lng >= minLng && lng <= maxLng;
}

function hashToBucket(str, total) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % total;
}

function gridCategoryFileExists(gridName, category, source = 'cat') {
  return logExecutionTimeSync(
    _gridCategoryFileExistsInner,
    'gridCategoryFileExists',
    gridName,
    '',
    gridName,
    category,
    source
  );
}

function _gridCategoryFileExistsInner(gridName, category, source) {
  const folder = source === 'bestcat' ? path.join(MAPS_DIR, 'bestcat_json') : LINKS_FOLDER;
  const safeCategory = category.replace(/[^a-zA-Z0-9]/g, '_');
  const safeGridName = gridName.replace(/[^a-zA-Z0-9]/g, '_');
  const filePath = path.join(folder, `grid_${safeGridName}_${safeCategory}.json`);
  return fs.existsSync(filePath);
}

function shuffleInPlace(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

// === File Operations with Timing ===
function loadProgress() {
  return logExecutionTimeSync(_loadProgressInner, 'loadProgress', '', '');
}

function _loadProgressInner() {
  if (fs.existsSync(PROGRESS_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(PROGRESS_FILE));
    } catch (err) {
      console.error(`❌ Error loading progress file: ${err.message}`);
      return {};
    }
  }
  return {};
}

function saveProgress(progress) {
  return logExecutionTimeSync(_saveProgressInner, 'saveProgress', '', '', progress);
}

function _saveProgressInner(progress) {
  ensureDirExists(PROGRESS_FILE);
  try {
    fs.writeFileSync(PROGRESS_FILE, JSON.stringify(progress, null, 2));
  } catch (err) {
    console.error(`❌ Error saving progress file: ${err.message}`);
  }
}

function loadSeenPlaceIds() {
  return logExecutionTimeSync(_loadSeenPlaceIdsInner, 'loadSeenPlaceIds', '', '');
}

function _loadSeenPlaceIdsInner() {
  const seenPlaceIds = new Set();
  if (fs.existsSync(SEEN_IDS_FILE)) {
    try {
      JSON.parse(fs.readFileSync(SEEN_IDS_FILE)).forEach(id => {
        if (id) seenPlaceIds.add(id);
      });
    } catch (err) {
      console.error(`❌ Error loading seen place IDs: ${err.message}`);
    }
  }
  if (fs.existsSync(COMBINED_URLS_FILE)) {
    try {
      JSON.parse(fs.readFileSync(COMBINED_URLS_FILE)).forEach(url => {
        const id = _getPlaceIdInner(url);
        if (id) seenPlaceIds.add(id);
      });
    } catch (err) {
      console.error(`❌ Error loading combined URLs: ${err.message}`);
    }
  }
  console.log(`📊 Loaded ${seenPlaceIds.size} seen place IDs from disk`);
  return seenPlaceIds;
}

function loadSeenPlaceIdsBloom() {
  return logExecutionTimeSync(
    _loadSeenPlaceIdsBloomInner, 
    'loadSeenPlaceIdsBloom', 
    '', 
    '', 
    BLOOM_EXPECTED_ITEMS, 
    BLOOM_ERROR_RATE
  );
}

function _loadSeenPlaceIdsBloomInner(expectedItems, errorRate) {
  let bloom;
  if (fs.existsSync(BLOOM_FILE)) {
    try {
      const json = JSON.parse(fs.readFileSync(BLOOM_FILE));
      bloom = BloomFilter.fromJSON(json);
      console.log(`📊 Loaded Bloom filter with size: ${bloom.size}`);
    } catch (err) {
      console.error(`❌ Error loading Bloom filter: ${err.message}`);
      bloom = new BloomFilter(expectedItems, errorRate);
    }
  } else {
    bloom = new BloomFilter(expectedItems, errorRate);
  }
  
  // Load exact place IDs if we're using secondary verification
  if (ENABLE_SECONDARY_VERIFICATION) {
    const seenIds = _loadSeenPlaceIdsInner();
    seenIds.forEach(id => {
      if (id) exactPlaceIds.add(id);
    });
    console.log(`📊 Secondary verification loaded ${exactPlaceIds.size} exact place IDs`);
  }
  
  return bloom;
}

function saveSeenPlaceIdsBloom(bloom) {
  return logExecutionTimeSync(_saveSeenPlaceIdsBloomInner, 'saveSeenPlaceIdsBloom', '', '', bloom);
}

function _saveSeenPlaceIdsBloomInner(bloom) {
  ensureDirExists(BLOOM_FILE);
  try {
    fs.writeFileSync(BLOOM_FILE, JSON.stringify(bloom.saveAsJSON(), null, 2));
    console.log(`💾 Saved Bloom filter with size: ${bloom.size}`);
    
    // If we're using secondary verification, also save exact IDs
    if (ENABLE_SECONDARY_VERIFICATION && exactPlaceIds.size > 0) {
      saveSeenPlaceIds(exactPlaceIds);
    }
  } catch (err) {
    console.error(`❌ Error saving Bloom filter: ${err.message}`);
  }
}

function saveSeenPlaceIds(seenPlaceIds) {
  return logExecutionTimeSync(_saveSeenPlaceIdsInner, 'saveSeenPlaceIds', '', '', seenPlaceIds);
}

function _saveSeenPlaceIdsInner(seenPlaceIds) {
  ensureDirExists(SEEN_IDS_FILE);
  try {
    fs.writeFileSync(SEEN_IDS_FILE, JSON.stringify([...seenPlaceIds], null, 2));
    console.log(`💾 Saved ${seenPlaceIds.size} exact place IDs`);
  } catch (err) {
    console.error(`❌ Error saving seen place IDs: ${err.message}`);
  }
}

// === Custom Bloom Filter Methods with Timing ===
// We need to extend the BloomFilter prototype to add our monitoring functions
const originalBloomFilterHas = BloomFilter.prototype.has;
BloomFilter.prototype.has = function(element, gridName = '', level = '') {
  const start = Date.now();
  const result = originalBloomFilterHas.call(this, element);
  const duration = Date.now() - start;
  const line = `${new Date().toISOString()},${gridName},${level},bloomFilter.has,${duration}\n`;
  fs.appendFileSync(FUNCTION_TIMES_CSV, line);
  return result;
};

const originalBloomFilterAdd = BloomFilter.prototype.add;
BloomFilter.prototype.add = function(element, gridName = '', level = '') {
  const start = Date.now();
  const result = originalBloomFilterAdd.call(this, element);
  const duration = Date.now() - start;
  const line = `${new Date().toISOString()},${gridName},${level},bloomFilter.add,${duration}\n`;
  fs.appendFileSync(FUNCTION_TIMES_CSV, line);
  return result;
};

// Secondary verification for Bloom filter
function verifyDuplicateWithSecondaryMethod(placeId) {
  if (!placeId) return false;
  return exactPlaceIds.has(placeId);
}

// Add a place ID to secondary verification
function addToSecondaryVerification(placeId) {
  if (!placeId) return;
  exactPlaceIds.add(placeId);
}

// === Browser Management Functions ===
async function launchSharedBrowser(numTabs = 10) {
  return await logExecutionTime(_launchSharedBrowserInner, 'launchSharedBrowser', '', '', numTabs);
}

async function _launchSharedBrowserInner(numTabs) {
  if (browser) return { browser, tabs }; // already initialized
  try {
    if (fs.existsSync(PUPPETEER_PROFILE_DIR)) {
      fs.rmSync(PUPPETEER_PROFILE_DIR, { recursive: true, force: true });
    }
  } catch (err) {
    console.warn('⚠️ Failed to delete old temp profile:', err.message);
  }
  
  const launchOptions = {
    headless: HEADLESS,
    userDataDir: PUPPETEER_PROFILE_DIR,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--window-size=1920,1080',
      '--start-maximized',
      '--disable-dev-shm-usage',
      '--disable-blink-features=AutomationControlled',
      '--enable-webgl',
      '--use-gl=swiftshader'
    ]
  };
  
  try {
    browser = await puppeteer.launch(launchOptions);
  } catch (err) {
    console.error(`❌ Failed to launch browser: ${err.message}`);
    // Try again with minimal options
    console.log('🔄 Trying again with minimal options...');
    launchOptions.args = ['--no-sandbox', '--disable-setuid-sandbox'];
    browser = await puppeteer.launch(launchOptions);
  }
  
  tabs = [];
  for (let i = 0; i < numTabs; i++) {
    try {
      const page = await browser.newPage();
      await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64)...');
      await page.setViewport({ width: 1280, height: 800 });
      await page.evaluateOnNewDocument(() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        window.chrome = {
          runtime: {},
          loadTimes: () => {},
          csi: () => {},
          app: { isInstalled: false }
        };
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (params) =>
          params.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(params);
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
      });
      tabs.push(page);
    } catch (err) {
      console.error(`❌ Failed to create tab ${i}: ${err.message}`);
    }
  }
  
  if (tabs.length === 0) {
    throw new Error('Failed to create any browser tabs');
  }
  
  return { browser, tabs };
}

function getBrowserTab(workerId) {
  return tabs[workerId % tabs.length];
}

async function closeBrowserPool() {
  return await logExecutionTime(_closeBrowserPoolInner, 'closeBrowserPool', '', '');
}

async function _closeBrowserPoolInner() {
  if (browser) {
    try {
      await browser.close();
      browser = null;
      tabs = [];
      const tmp = require('os').tmpdir();
      const userDataDir = path.join(tmp, 'puppeteer-temp-profile');
      try {
        fs.rmSync(userDataDir, { recursive: true, force: true });
        console.log('🧹 Cleaned up Puppeteer temp profile directory');
      } catch (err) {
        console.warn('⚠️ Failed to remove temp profile dir:', err.message);
      }
    } catch (err) {
      console.error(`❌ Error closing browser: ${err.message}`);
    }
  }
}

// === File Writing Functions with Timing ===
function appendToFileWithHeader(filePath, line, header) {
  return logExecutionTimeSync(_appendToFileWithHeaderInner, 'appendToFileWithHeader', '', '', filePath, line, header);
}

function _appendToFileWithHeaderInner(filePath, line, header) {
  ensureDirExists(filePath);
  const prependHeader = !fs.existsSync(filePath);
  try {
    fs.appendFileSync(filePath, prependHeader ? header + line : line);
  } catch (err) {
    console.error(`❌ Error appending to file ${filePath}: ${err.message}`);
  }
}

function appendToErrorCSV(grid, category) {
  return logExecutionTimeSync(_appendToErrorCSVInner, 'appendToErrorCSV', grid, '', grid, category);
}

function _appendToErrorCSVInner(grid, category) {
  appendToFileWithHeader(ERROR_CSV_FILE, `${grid},${category}\n`, 'grid,category\n');
}

function appendToNoLinksCSV(grid, category) {
  return logExecutionTimeSync(_appendToNoLinksCSVInner, 'appendToNoLinksCSV', grid, '', grid, category);
}

function _appendToNoLinksCSVInner(grid, category) {
  appendToFileWithHeader(NO_LINKS_CSV_FILE, `${grid},${category}\n`, 'grid,category\n');
}

function appendToCopiesCSV(grid, category) {
  return logExecutionTimeSync(_appendToCopiesCSVInner, 'appendToCopiesCSV', grid, '', grid, category);
}

function _appendToCopiesCSVInner(grid, category) {
  appendToFileWithHeader(COPIES_CSV_FILE, `${grid},${category}\n`, 'grid,category\n');
}

function appendToRemovedCategoriesCSV(entry) {
  return logExecutionTimeSync(_appendToRemovedCategoriesCSVInner, 'appendToRemovedCategoriesCSV', '', '', entry);
}

function _appendToRemovedCategoriesCSVInner(entry) {
  const line = `${entry.category},${entry.grid},${entry.repeat_count}\n`;
  appendToFileWithHeader(REMOVED_CATEGORIES_FILE, line, 'category,grid,repeat_count\n');
}

function appendNewLinksToFile(newLinks, gridName = '', level = '') {
  return logExecutionTimeSync(_appendNewLinksToFileInner, 'appendNewLinksToFile', gridName, level, newLinks);
}
function _appendNewLinksToFileInner(newLinks) {
  if (!newLinks || newLinks.length === 0) return;
  
  try {
    ensureDirExists(NEW_LINKS_FILE);
    
    // Remove duplicates in this batch
    const uniqueLinks = Array.from(new Set(newLinks)).filter(link => link && typeof link === 'string');
    
    let allLinks = [];
    
    // Try to read existing links
    if (fs.existsSync(NEW_LINKS_FILE)) {
      try {
        const fileContent = fs.readFileSync(NEW_LINKS_FILE, 'utf8');
        if (fileContent.trim()) {
          // Check if it's a JSON array
          if (fileContent.trim().startsWith('[')) {
            allLinks = JSON.parse(fileContent);
          } else {
            // It might be JSONL format, try to parse each line
            allLinks = fileContent.split('\n')
              .filter(line => line.trim())
              .map(line => {
                try {
                  const parsed = JSON.parse(line);
                  return parsed.link || null;
                } catch (e) {
                  return null;
                }
              })
              .filter(Boolean);
          }
        }
      } catch (error) {
        console.warn(`⚠️ Could not parse ${NEW_LINKS_FILE}, starting fresh: ${error.message}`);
        // File exists but is corrupt, we'll overwrite it
      }
    }
    
    // Add new links and remove duplicates again
    allLinks = [...allLinks, ...uniqueLinks];
    allLinks = Array.from(new Set(allLinks));
    
    // Write as a proper JSON array
    fs.writeFileSync(NEW_LINKS_FILE, JSON.stringify(allLinks, null, 2));
    console.log(`✅ Added ${uniqueLinks.length} unique links, total: ${allLinks.length}`);
    
  } catch (e) {
    console.error('❌ Failed to update new_links.json:', e.message);
  }
}
function savePerGridLinks(gridName, category, links, source = 'cat') {
  return logExecutionTimeSync(_savePerGridLinksInner, 'savePerGridLinks', gridName, '', gridName, category, links, source);
}

function _savePerGridLinksInner(gridName, category, links, source) {
  const targetFolder = source === 'bestcat'
    ? path.join(MAPS_DIR, 'bestcat_json')
    : LINKS_FOLDER;
    
  try {
    if (!fs.existsSync(targetFolder)) {
      fs.mkdirSync(targetFolder, { recursive: true });
    }
    const safeCategory = category.replace(/[^a-zA-Z0-9]/g, '_');
    const safeGridName = gridName.replace(/[^a-zA-Z0-9]/g, '_');
    const filename = `grid_${safeGridName}_${safeCategory}.json`;
    const filePath = path.join(targetFolder, filename);
    fs.writeFileSync(filePath, JSON.stringify(links, null, 2));
  } catch (err) {
    console.error(`❌ Error saving grid links: ${err.message}`);
  }
}

function appendToStatsCSV(row) {
  return logExecutionTimeSync(_appendToStatsCSVInner, 'appendToStatsCSV', row.grid || '', '', row);
}

function _appendToStatsCSVInner(row) {
  try {
    ensureDirExists(STATS_CSV_FILE);
    const key = `${row.grid}|${row.category}`;
    let records = [];
    let headersSet = new Set(Object.keys(row));
    let updated = false;
    
    if (fs.existsSync(STATS_CSV_FILE)) {
      const content = fs.readFileSync(STATS_CSV_FILE, 'utf-8').trim().split('\n');
      const csvHeaders = content[0].split(',');
      for (let i = 1; i < content.length; i++) {
        const values = content[i].split(',');
        const record = {};
        csvHeaders.forEach((h, idx) => { record[h] = values[idx]; });
        if (`${record.grid}|${record.category}` === key) {
          Object.assign(record, row);
          updated = true;
        }
        Object.keys(record).forEach(h => headersSet.add(h));
        records.push(record);
      }
    }
    
    if (!updated) records.push(row);
    const headers = Array.from(headersSet);
    const lines = [
      headers.join(','),
      ...records.map(rec => headers.map(h => rec[h] || '').join(','))
    ];
    fs.writeFileSync(STATS_CSV_FILE, lines.join('\n'));
  } catch (err) {
    console.error(`❌ Error appending to stats CSV: ${err.message}`);
  }
}

// === Data Loading Functions with Timing ===
async function loadCategories() {
  return await logExecutionTime(_loadCategoriesInner, 'loadCategories', '', '');
}

async function _loadCategoriesInner() {
  const catList = [];
  const loadFrom = (filename, source) => new Promise(resolve => {
    try {
      if (!fs.existsSync(filename)) {
        console.error(`❌ Categories file not found: ${filename}`);
        resolve();
        return;
      }
      
      fs.createReadStream(filename)
        .pipe(csv())
        .on('data', row => {
          if (row.type && row.type.trim()) {
            const cleaned = row.type.replace(/"+/g, '').trim();
            if (cleaned) catList.push({ name: cleaned, source });
          }
        })
        .on('error', err => {
          console.error(`❌ Error reading categories: ${err.message}`);
          resolve();
        })
        .on('end', resolve);
    } catch (err) {
      console.error(`❌ Error setting up categories stream: ${err.message}`);
      resolve();
    }
  });
  
  await loadFrom('cat.csv', 'cat');
  const seen = new Set();
  const unique = [];
  for (const item of catList) {
    if (!seen.has(item.name)) {
      seen.add(item.name);
      unique.push(item);
    }
  }
  
  console.log(`📊 Loaded ${unique.length} unique categories`);
  return unique;
}

// === Navigation and Page Interaction Functions with Timing ===
async function rejectConsentForm(page, gridName = '', level = '') {
  return await logExecutionTime(_rejectConsentFormInner, 'rejectConsentForm', gridName, level, page);
}

async function _rejectConsentFormInner(page) {
  try {
    const formHandle = await page.$('form[action*="/consent.google.com/save"]');
    if (!formHandle) return false;
    await page.evaluate(form => form.submit(), formHandle);
    await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 });
    return true;
  } catch (err) {
    console.warn(`⚠️ Error handling consent form: ${err.message}`);
    return false;
  }
}

async function safeGoto(page, url, retries = 3, gridName = '', level = '') {
  return await logExecutionTime(_safeGotoInner, 'safeGoto', gridName, level, page, url, retries);
}

async function _safeGotoInner(page, url, retries = 3) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      await page.goto(url, { waitUntil: 'networkidle2', timeout: NAVIGATION_TIMEOUT });
      await _rejectConsentFormInner(page);
      await page.waitForSelector('body', { timeout: 25000 });
      return true;
    } catch (err) {
      console.warn(`⚠️ Navigation attempt ${attempt} failed: ${err.message}`);
      if (attempt === retries) throw err;
      await new Promise(res => setTimeout(res, 1500));
    }
  }
  throw new Error(`Failed to navigate to ${url} after ${retries} attempts`);
}

async function autoScroll(page, maxScrolls = 40, gridName = '', level = '') {
  return await logExecutionTime(_autoScrollInner, 'autoScroll', gridName, level, page, maxScrolls);
}

async function _autoScrollInner(page, maxScrolls = 40) {
  try {
    const isPlacePage = await page.$('h1[class*="DUwDvf"]');
    if (isPlacePage) {
      console.log(`⚠️ Direct place page detected`);
      return 'DIRECT_PLACE_PAGE';
    }
    
    const containerSelector = 'div[role="feed"]';
    
    // Wait for scroll container with multiple attempts
    let scrollContainer = null;
    for (let i = 0; i < 5; i++) {
      scrollContainer = await page.$(containerSelector);
      if (scrollContainer) break;
      console.log(`⏳ Waiting for scroll container... attempt ${i + 1}`);
      await delay(1000);
    }
    
    if (!scrollContainer) {
      console.error('❌ Scroll container not found!');
      return 'NO_SCROLL_CONTAINER';
    }
    
    let previousHeight = 0;
    let stuckCounter = 0;
    
    for (let i = 0; i < maxScrolls; i++) {
      try {
        const currentHeight = await page.evaluate(el => el.scrollHeight, scrollContainer);
        await page.evaluate(el => {
          el.scrollBy(0, el.clientHeight || 800);
        }, scrollContainer);
        await delay(1000);
        
        const newHeight = await page.evaluate(el => el.scrollHeight, scrollContainer);
        await page.evaluate(el => {
          el.scrollBy(0, 300);
        }, scrollContainer);
        
        if (newHeight === previousHeight) {
          stuckCounter++;
          if (stuckCounter >= 2) break;
        } else {
          stuckCounter = 0;
        }
        
        previousHeight = newHeight;
      } catch (err) {
        console.warn(`⚠️ Error during scrolling: ${err.message}`);
        break;
      }
    }
    
    return 'SCROLLING_COMPLETE';
  } catch (err) {
    console.error(`❌ Error in autoScroll: ${err.message}`);
    return 'SCROLLING_ERROR';
  }
}

async function delay(ms) {
  return new Promise(res => setTimeout(res, ms));
}

// === Queue Management ===
const statsWriteQueue = new PQueue({ concurrency: 1 });
const progressWriteQueue = new PQueue({ concurrency: 1 });

function queueAppendStats(row) {
  statsWriteQueue.add(() => appendToStatsCSV(row));
}

function queueSaveProgress(progress) {
  ensureDirExists(PROGRESS_FILE);
  progressWriteQueue.add(() => fs.writeFileSync(PROGRESS_FILE, JSON.stringify(progress, null, 2)));
}

// === Main Scrape Function (timed) ===
async function scrapeGridWorker(gridCells, categories, workerId, seenPlaceIdsBloom, categoryStats, options = {}, page) {
  const scrapeStart = Date.now();
  let totalInside = 0;
  let uniqueInside = 0;
  let totalOutside = 0;
  const startTime = Date.now(); 
  let durationMin = 0;
  
  try {
    await page.setDefaultNavigationTimeout(NAVIGATION_TIMEOUT);
  } catch (err) {
    console.warn(`⚠️ Could not set navigation timeout: ${err.message}`);
  }
  
  let gridUniqueCount = 0;
  let gridRepeatCount = 0;
  let falsePositiveCount = 0;
  
  for (let grid of gridCells) {
    const gridName = grid.name;
    const level = grid.level;
    const [lat, lng] = grid.center;
    const [corner1, , corner3] = grid.box_corners;
    const gridHeight = Math.abs(corner1[0] - corner3[0]);
    const gridWidth = Math.abs(corner1[1] - corner3[1]);
    const minLat = lat - 1.5 * gridHeight;
    const maxLat = lat + 1.5 * gridHeight;
    const minLng = lng - 1.5 * gridWidth;
    const maxLng = lng + 1.5 * gridWidth;
    
    for (let { name: category } of categories) {
      // Time file existence check
      const fileExists = logExecutionTimeSync(
        _gridCategoryFileExistsInner, 
        'gridCategoryFileExists',
        gridName,
        level,
        gridName,
        category
      );
      
      if (fileExists) {
        console.log(`⏭️ Skipping ${gridName} | ${category} — data file already exists`);
        const statsRow = {
          grid: gridName,
          category,
          total: 0,
          unique: 0,
          repeat: 'SKIPPED',
          time: 0,
          total_inside: 0,
          unique_inside: 0,
          total_outside: 0,
          skipped_due_to_file: true
        };
        queueAppendStats(statsRow);
        return {
          grid: gridCells[0],
          businessesFound: 0,
          categoriesWithLinks: 0,
          totalExtracted: 0,
          uniqueExtracted: 0,
          durationMin: 0,
          category,
          skipped_due_to_file: true
        };
      }
      
      const catStart = Date.now();
      const encoded = encodeURIComponent(category);
      const cityTag = (grid.tags && grid.tags.length > 0) ? `+en+${encodeURIComponent(grid.tags[0])}` : '';
      const searchUrl = `https://www.google.com/maps/search/${encoded}${cityTag}/@${lat},${lng},15.5z`;
      console.log(`🧵 Worker ${workerId} | Grid ${gridName} | Searching: ${category}`);
      
      let newLinks = [];
      let allLinks = [];
      let tagLinks = [];
      
      try {
        await safeGoto(page, searchUrl, 3, gridName, level);
        const scrollResult = await autoScroll(page, 40, gridName, level);
        
        if (scrollResult === 'DIRECT_PLACE_PAGE') {
          await logExecutionTimeSync(
            _appendToNoLinksCSVInner,
            'appendToNoLinksCSV',
            gridName,
            level,
            gridName,
            category
          );
          console.log(`ℹ️ Direct place page detected for ${gridName} | ${category}`);
          continue;
        }
        
        if (scrollResult === 'NO_SCROLL_CONTAINER') {
          await logExecutionTimeSync(
            _appendToNoLinksCSVInner,
            'appendToNoLinksCSV',
            gridName,
            level,
            gridName,
            category
          );
          console.log(`⚠️ No scroll container found for ${gridName} | ${category}`);
          continue;
        }
        
        try {
          await logExecutionTime(
            (...args) => page.waitForSelector(...args),
            'page.waitForSelector',
            gridName,
            level,
            'a.hfpxzc',
            { timeout: 30000 }
          );
        } catch (err) {
          console.warn(`⚠️ No links found on page for ${gridName} | ${category}: ${err.message}`);
          await logExecutionTimeSync(
            _appendToNoLinksCSVInner,
            'appendToNoLinksCSV',
            gridName,
            level,
            gridName,
            category
          );
          continue;
        }
        
        const links = await logExecutionTime(
          () => page.evaluate(() => Array.from(document.querySelectorAll('a.hfpxzc')).map(a => a.href)),
          'page.evaluate.links',
          gridName,
          level
        );
        
        console.log(`📊 Found ${links.length} links in ${gridName} | ${category}`);
        
        if (!links || links.length === 0) {
          await logExecutionTimeSync(
            _appendToNoLinksCSVInner,
            'appendToNoLinksCSV',
            gridName,
            level,
            gridName,
            category
          );
          console.log(`⚠️ No links found for ${gridName} | ${category}`);
          continue;
        }
        
        for (const link of links) {
          // Skip invalid links
          if (!link || typeof link !== 'string') continue;
          
          // Time the extraction of coordinates from URL
          const coords = await logExecutionTimeSync(
            _extractCoordsFromUrlInner,
            'extractCoordsFromUrl',
            gridName, 
            level,
            link
          );
          
          let inside = false;
          
          if (coords) {
            // Time the bounding box check
            inside = await logExecutionTimeSync(
              _isInsideBoundingBoxInner,
              'isInsideBoundingBox',
              gridName,
              level,
              ...coords, minLat, maxLat, minLng, maxLng
            );
            
            if (inside) {
              totalInside++;
            } else {
              totalOutside++;
            }
          } else {
            totalOutside++;
          }
          
          // Time the extraction of place ID
          const placeId = await logExecutionTimeSync(
            _getPlaceIdInner, 
            'getPlaceId', 
            gridName, 
            level, 
            link
          );
          
          if (!placeId) {
            console.warn(`⚠️ Could not extract place ID from link: ${link.substring(0, 50)}...`);
            continue;
          }
          
          // Debug logging for Bloom filter
          console.log(`🔍 Checking placeId: ${placeId.substring(0, 8)}..., filter size: ${seenPlaceIdsBloom.size}`);
          
          // Check if this is a duplicate
          let isRepeat = false;
          
          // First, check the Bloom filter
          const bloomFilterIndicatesSeen = seenPlaceIdsBloom.has(placeId, gridName, level);
          console.log(`🔍 Result for ${placeId.substring(0, 8)}... - Bloom filter indicates seen: ${bloomFilterIndicatesSeen}`);
          
          if (bloomFilterIndicatesSeen && ENABLE_SECONDARY_VERIFICATION) {
            // Possible false positive - verify with secondary method
            const isRealDuplicate = verifyDuplicateWithSecondaryMethod(placeId);
            
            if (!isRealDuplicate) {
              // It was a false positive!
              console.log(`⚠️ Bloom filter false positive corrected: ${placeId.substring(0, 8)}...`);
              logFalsePositive(placeId, gridName, level, 'FALSE_POSITIVE_CORRECTED');
              falsePositiveCount++;
              
              // Proceed as a unique link
              seenPlaceIdsBloom.add(placeId, gridName, level);
              addToSecondaryVerification(placeId);
              
              console.log(`✨ New unique place found: ${placeId.substring(0, 8)}... in ${gridName} | ${category}`);
              newLinks.push(link);
              allLinks.push(link);
              tagLinks.push(link);
              gridUniqueCount++;
              if (inside) uniqueInside++;
            } else {
              // Confirmed duplicate
              isRepeat = true;
              console.log(`♻️ Confirmed repeat place: ${placeId.substring(0, 8)}... in ${gridName} | ${category}`);
              gridRepeatCount++;
              allLinks.push('REPEAT');
              tagLinks.push('REPEAT');
            }
          } else if (!bloomFilterIndicatesSeen) {
            // New unique place - not in Bloom filter
            seenPlaceIdsBloom.add(placeId, gridName, level);
            if (ENABLE_SECONDARY_VERIFICATION) {
              addToSecondaryVerification(placeId);
            }
            
            console.log(`✨ New unique place found: ${placeId.substring(0, 8)}... in ${gridName} | ${category}`);
            newLinks.push(link);
            allLinks.push(link);
            tagLinks.push(link);
            gridUniqueCount++;
            if (inside) uniqueInside++;
          } else {
            // Bloom filter indicates seen, no secondary verification
            isRepeat = true;
            console.log(`♻️ Repeat place: ${placeId.substring(0, 8)}... in ${gridName} | ${category}`);
            gridRepeatCount++;
            allLinks.push('REPEAT');
            tagLinks.push('REPEAT');
          }
        }
        
        // Time saving links to grid-specific file
        await logExecutionTimeSync(
          _savePerGridLinksInner,
          'savePerGridLinks',
          gridName,
          level,
          gridName,
          category,
          tagLinks
        );
        
        // Time appending new links to global file
        await logExecutionTimeSync(
          _appendNewLinksToFileInner,
          'appendNewLinksToFile',
          gridName,
          level,
          newLinks
        );
        
        // Update category statistics
        if (!categoryStats[category]) {
          categoryStats[category] = {
            grids_ran: 0,
            grids_successful: 0,
            total_unique_links: 0,
            repeat_rate_sum: 0
          };
        }
        
        categoryStats[category].grids_ran += 1;
        if (newLinks.length > 0) categoryStats[category].grids_successful += 1;
        categoryStats[category].total_unique_links += newLinks.length;
        
        const totalLinks = newLinks.length + gridRepeatCount;
        const repetitionRate = totalLinks > 0 ? (gridRepeatCount / totalLinks).toFixed(2) : '0.00';
        categoryStats[category].repeat_rate_sum += parseFloat(repetitionRate);
        
        const elapsed = getElapsedMinutes(Date.now() - catStart);
        const chunkStats = [];
        const seenInChunk = new Set();
        
        for (let i = 0; i < allLinks.length; i += 10) {
          const chunk = allLinks.slice(i, i + 10);
          let chunkRepeats = 0;
          const chunkSeen = new Set();
          
          for (let link of chunk) {
            if (link === 'REPEAT') {
              chunkRepeats++;
            } else {
              const id = await logExecutionTimeSync(
                _getPlaceIdInner, 
                'getPlaceId.chunk', 
                gridName, 
                level, 
                link
              );
              
              if (!id || chunkSeen.has(id)) chunkRepeats++;
              else chunkSeen.add(id);
            }
          }
          
          chunkStats.push(chunkRepeats);
        }
        
        durationMin = (Date.now() - startTime) / 60000;
        
        const statsRow = {
          grid: gridName,
          category,
          total: allLinks.length,
          unique: newLinks.length,
          repeat: repetitionRate,
          time: elapsed,
          total_inside: totalInside,
          unique_inside: uniqueInside,
          total_outside: totalOutside,
          false_positives_corrected: falsePositiveCount
        };
        
        chunkStats.forEach((rep, idx) => {
          statsRow[`chunk_${idx * 10 + 1}-${idx * 10 + 10}_repeat`] = rep;
        });
        
        // Check for consecutive 100% repeat chunks
        if (options.layer2Mode || options.layer3Mode) {
          for (let i = 0; i < chunkStats.length - 1; i++) {
            if (chunkStats[i] === 10 && chunkStats[i + 1] === 10) {
              console.log(`🚫 Skipping ${gridName} | ${category} due to 2 consecutive 100% repeat chunks`);
              
              const statsRow = {
                grid: gridName,
                category,
                total: allLinks.length,
                unique: newLinks.length,
                repeat: 'CHUNK_SKIP',
                time: getElapsedMinutes(Date.now() - catStart),
                total_inside: totalInside,
                unique_inside: uniqueInside,
                total_outside: totalOutside,
                false_positives_corrected: falsePositiveCount,
                skipped_due_to_chunks: true
              };
              
              chunkStats.forEach((rep, idx) => {
                statsRow[`chunk_${idx * 10 + 1}-${idx * 10 + 10}_repeat`] = rep;
              });
              
              queueAppendStats(statsRow);
              
              return {
                grid: gridCells[0],
                businessesFound: 0,
                categoriesWithLinks: 0,
                totalExtracted: gridUniqueCount + gridRepeatCount,
                uniqueExtracted: gridUniqueCount,
                durationMin,
                category: categories[0].name,
                skipped_due_to_chunks: true
              };
            }
          }
        }
        
        queueAppendStats(statsRow);
        
        // Handle early abort for Layer 2
        if (options.layer2Mode) {
          if (newLinks.length === 0) {
            options.l2NoUniqueCounter[category] = (options.l2NoUniqueCounter[category] || 0) + 1;
            if (options.l2NoUniqueCounter[category] >= L2_NO_UNIQUE_LIMIT) {
              console.log(`🚫 L2 early abort for ${category} — ${L2_NO_UNIQUE_LIMIT} grids with no unique results`);
              options.abortL2[category] = true;
            }
          } else {
            options.l2NoUniqueCounter[category] = 0;
          }
        }
        
        // Handle early abort for Layer 3
        if (options.layer3Mode) {
          if (newLinks.length === 0) {
            options.l3NoUniqueCounter[category] = (options.l3NoUniqueCounter[category] || 0) + 1;
            if (options.l3NoUniqueCounter[category] >= L3_NO_UNIQUE_LIMIT) {
              console.log(`🚫 L3 early abort for ${category} — ${L3_NO_UNIQUE_LIMIT} grids with no unique results`);
              options.abortL3[category] = true;
            }
          } else {
            options.l3NoUniqueCounter[category] = 0;
          }
        }
        
        // Record grids with no links
        if (newLinks.length === 0) {
          await logExecutionTimeSync(
            _appendToNoLinksCSVInner,
            'appendToNoLinksCSV',
            gridName,
            level,
            gridName,
            category
          );
        } 
        
        // Always show the result, whether there are new links or not
        console.log(`✅ Grid ${gridName} | ${category} | New: ${newLinks.length} | Total: ${allLinks.length} | % Repeat: ${repetitionRate} | False Positives: ${falsePositiveCount} | Time: ${elapsed} min`);
        
        
      } catch (err) {
        console.error(`❌ Error in ${gridName} | ${category}: ${err.message}`);
        
        await logExecutionTimeSync(
          _appendToErrorCSVInner,
          'appendToErrorCSV',
          gridName,
          level,
          gridName,
          category
        );
        
        await logExecutionTimeSync(
          _savePerGridLinksInner,
          'savePerGridLinks.error',
          gridName,
          level,
          gridName,
          category,
          [],
          'cat'
        );
      }
    }
  }
  
  // Time total scraping duration
  const scrapeDuration = Date.now() - scrapeStart;
  fs.appendFileSync(
    FUNCTION_TIMES_CSV,
    `${new Date().toISOString()},${gridCells[0].name},${gridCells[0].level},scrapeGridWorker.total,${scrapeDuration}\n`
  );
  
  return {
    grid: gridCells[0],
    businessesFound: gridUniqueCount,
    categoriesWithLinks: gridUniqueCount > 0 ? 1 : 0,
    totalExtracted: gridUniqueCount + gridRepeatCount,
    uniqueExtracted: gridUniqueCount,
    falsePositivesFixed: falsePositiveCount,
    durationMin,
    category: categories[0].name,
  };
}

async function runWithThreadPool(jobs, numWorkers, handler) {
  const poolStart = Date.now();
  let index = 0;
  const results = [];

  async function launchWorkerBrowser(workerId) {
    return await logExecutionTime(
      async () => {
        try {
          const launchOptions = {
            headless: HEADLESS,
            args: [
              '--no-sandbox',
              '--disable-setuid-sandbox',
              '--disable-gpu',
              '--window-size=1920,1080',
              '--disable-dev-shm-usage',
              '--disable-blink-features=AutomationControlled'
            ]
          };
          
          const browser = await puppeteer.launch(launchOptions);
          const page = await browser.newPage();
          await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64)...');
          await page.setViewport({ width: 1280, height: 800 });

          await page.evaluateOnNewDocument(() => {
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            window.chrome = { runtime: {}, loadTimes: () => {}, csi: () => {}, app: { isInstalled: false } };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4] });
          });

          return { browser, page };
        } catch (err) {
          console.error(`❌ Failed to launch worker browser ${workerId}: ${err.message}`);
          throw err;
        }
      },
      'launchWorkerBrowser',
      '',
      '',
      workerId
    );
  }

  async function worker(workerId) {
    let browser = null;
    let page = null;
    
    try {
      const browserObj = await launchWorkerBrowser(workerId);
      browser = browserObj.browser;
      page = browserObj.page;
    } catch (err) {
      console.error(`❌ Worker ${workerId} could not launch browser: ${err.message}`);
      return;
    }

    while (index < jobs.length) {
      const currentIndex = index++;
      const job = jobs[currentIndex];
      if (!job) break;

      try {
        const result = await logExecutionTime(
          async () => await handler(job, workerId, page),
          'handler',
          job.grid?.name || '',
          job.grid?.level || '',
        );

        results.push({ ...result, ...job });

        // === Restart logic ===
        jobsSinceRestart++;
        if (result && typeof result.uniqueExtracted === 'number') {
          newLinksSinceRestart += result.uniqueExtracted;
        }
        if (jobsSinceRestart >= RESTART_AFTER_JOBS) {
          if (browser) await browser.close();
          restartProcess();
          return;
        }
        // === End restart logic ===

      } catch (err) {
        console.error(`❌ Worker ${workerId} job failed: ${err.message}`);
        logExecutionTimeSync(
          () => {},
          'worker.error',
          job.grid?.name || '',
          job.grid?.level || '',
        );
        
        // Try to restart the browser if it crashes
        try {
          if (browser) await browser.close();
          const browserObj = await launchWorkerBrowser(workerId);
          browser = browserObj.browser;
          page = browserObj.page;
        } catch (browserErr) {
          console.error(`❌ Worker ${workerId} could not relaunch browser: ${browserErr.message}`);
          return; // Exit this worker if we can't relaunch the browser
        }
      }
    }

    if (browser) await browser.close();
  }

  const workers = [];
  for (let i = 0; i < numWorkers; i++) {
    workers.push(worker(i));
    await delay(1000); // Stagger worker starts
  }

  await Promise.all(workers);

  const poolDuration = Date.now() - poolStart;
  fs.appendFileSync(
    FUNCTION_TIMES_CSV,
    `${new Date().toISOString()},,ThreadPool,runWithThreadPool.total,${poolDuration}\n`
  );

  return results;
}
async function main() {
  const startTime = Date.now();
  
  // Log the start of the main function
  logExecutionTimeSync(() => {}, 'main.start', '', '');
  
  // Create output directory if it doesn't exist
  ensureDirExists(path.join(MAPS_DIR, 'dummy.txt'));
  console.log(`📁 Using output directory: ${MAPS_DIR}`);
  
  let categoryStats = {};
  
  console.log(`📊 Initializing Bloom filter with expectedItems=${BLOOM_EXPECTED_ITEMS}, errorRate=${BLOOM_ERROR_RATE}`);
  const seenPlaceIdsBloom = await logExecutionTime(loadSeenPlaceIdsBloom, 'loadSeenPlaceIdsBloom', '', '');
  
  console.log(`🔍 Bloom filter initialized with ${seenPlaceIdsBloom.size} items`);
  console.log(`🔧 Secondary verification ${ENABLE_SECONDARY_VERIFICATION ? 'ENABLED' : 'DISABLED'}`);
  
  if (ENABLE_SECONDARY_VERIFICATION) {
    console.log(`📊 Secondary verification has ${exactPlaceIds.size} items`);
  }
  
  // Load grid data with timing
  console.log(`📂 Loading grid data from ${GRID_FILE}`);
  let gridData;
  try {
    gridData = await logExecutionTimeSync(
      () => JSON.parse(fs.readFileSync(GRID_FILE)),
      'loadGridData',
      '',
      ''
    );
    console.log(`📊 Loaded grid data with ${gridData.layer1.length} layer 1 grids`);
  } catch (err) {
    console.error(`❌ Failed to load grid data: ${err.message}`);
    process.exit(1);
  }
  
  const allCategories = await loadCategories();
  if (!allCategories || allCategories.length === 0) {
    console.error('❌ No categories loaded! Check your category CSV file.');
    process.exit(1);
  }
  
  let progress = await loadProgress();
  ensureDirExists(PROGRESS_FILE);
  
  // Launch browser with timing
  try {
    const { browser: sharedBrowser, tabs: sharedTabs } = await launchSharedBrowser(NUM_WORKERS);
    browser = sharedBrowser;
    tabs = sharedTabs;
  } catch (err) {
    console.error(`❌ Failed to launch shared browser: ${err.message}`);
    console.log('🔄 Proceeding without shared browser - will create per-worker browsers');
  }
  
  const allL1Grids = gridData.layer1.map(g => ({ ...g, level: 'L1' }));
  const passedL1 = {};
  const passedL2 = {};
  const abortL2 = {};
  const abortL3 = {};
  const l2NoUniqueCounter = {};
  const l3NoUniqueCounter = {};
  
  // Reconstruct L1 passes from progress data
  await logExecutionTimeSync(
    () => {
      for (const { name: category } of allCategories) {
        passedL1[category] = new Set();
        for (const [gridName, record] of Object.entries(progress)) {
          const l1Key = `cat_${category}_level_L1`;
          if (record[l1Key]?.total_extracted >= LAYER1_THRESHOLD && record[l1Key]?.businesses_found > 0) {
            passedL1[category].add(gridName);
          }
        }
        console.log(`✅ Reconstructed L1 pass: ${category} — ${passedL1[category].size} grids`);
      }
    },
    'reconstructL1Passes',
    '',
    ''
  );
  
  // Generate Layer 1 jobs
  const jobsL1 = [];
  await logExecutionTimeSync(
    () => {
      for (const grid of allL1Grids) {
        for (const { name: category } of allCategories) {
          if (!progress[grid.name]?.[`cat_${category}_level_L1`]) {
            jobsL1.push({ grid, category });
          }
        }
      }
      // Shuffle the jobs for better distribution
      shuffleInPlace(jobsL1);
    },
    'generateL1Jobs',
    '',
    ''
  );
  
  if (!RUN_L2_ONLY && !RUN_L3_ONLY) {
    console.log(`🚀 Starting Layer 1 with ${jobsL1.length} jobs`);
    await runWithThreadPool(jobsL1, NUM_WORKERS, async ({ grid, category }, wid, page) => {
      const res = await scrapeGridWorker([grid], [{ name: category }], wid, seenPlaceIdsBloom, categoryStats, {}, page);
      progress[grid.name] = progress[grid.name] || {};
      progress[grid.name][`cat_${category}_level_L1`] = {
        total_extracted: res.totalExtracted,
        unique: res.uniqueExtracted,
        businesses_found: res.businessesFound,
        categories_with_links: res.categoriesWithLinks,
        false_positives_fixed: res.falsePositivesFixed || 0,
        level: 'L1'
      };
      
      if (res.totalExtracted >= LAYER1_THRESHOLD && res.businessesFound > 0) {
        passedL1[category].add(grid.name);
      }
      
      queueSaveProgress(progress);
      return res;
    });
    
    // Save progress after completing L1
    await saveProgress(progress);
    
    // Save bloom filter with timing
    await logExecutionTimeSync(
      () => saveSeenPlaceIdsBloom(seenPlaceIdsBloom),
      'saveSeenPlaceIdsBloom.afterL1',
      '',
      ''
    );
  }
  
  // Reconstruct L2 passes from progress data
  if (!SKIP_LAYER2 && !RUN_L3_ONLY) {
    await logExecutionTimeSync(
      () => {
        for (const { name: category } of allCategories) {
          passedL2[category] = new Set();
          for (const [gridName, record] of Object.entries(progress)) {
            const l2Key = `cat_${category}_level_L2`;
            if (record[l2Key]?.total_extracted >= LAYER2_THRESHOLD && record[l2Key]?.businesses_found > 0) {
              passedL2[category].add(gridName);
            }
          }
          console.log(`✅ Reconstructed L2 pass: ${category} — ${passedL2[category].size} grids`);
        }
      },
      'reconstructL2Passes',
      '',
      ''
    );
  }
  
  // Generate Layer 2 jobs
  const jobsL2 = [];
  await logExecutionTimeSync(
    () => {
      for (const { name: category } of allCategories) {
        if (!SKIP_LAYER2 && !RUN_L3_ONLY) {
          const l1Grids = RUN_L2_ONLY ? allL1Grids : allL1Grids.filter(g => passedL1[category]?.has(g.name));
          for (const l1 of l1Grids) {
            const l2s = l1.layer2 || [];
            for (const l2 of l2s) {
              if (!progress[l2.name]?.[`cat_${category}_level_L2`]) {
                jobsL2.push({ grid: { ...l2, level: 'L2', parent: l1.name }, category });
              }
            }
          }
        }
      }
      // Shuffle the jobs for better distribution
      shuffleInPlace(jobsL2);
    },
    'generateL2Jobs',
    '',
    ''
  );
  
  if (RUN_L2_ONLY || (!SKIP_LAYER2 && !RUN_L3_ONLY)) {
    console.log(`🧪 Starting Layer 2 with ${jobsL2.length} jobs`);
    await runWithThreadPool(jobsL2, NUM_WORKERS, async ({ grid, category }, wid, page) => {
      // Check if category has been marked for abort
      if (abortL2[category]) {
        console.log(`⏭️ Skipping ${grid.name} | ${category} due to category abort`);
        progress[grid.name] = progress[grid.name] || {};
        progress[grid.name][`cat_${category}_level_L2`] = {
          total_extracted: 0,
          unique: 0,
          businesses_found: 0,
          categories_with_links: 0,
          level: 'L2',
          skipped_due_to_abort: true
        };
        return {
          grid: grid,
          businessesFound: 0,
          categoriesWithLinks: 0,
          totalExtracted: 0,
          uniqueExtracted: 0,
          durationMin: 0,
          category: category,
          skipped_due_to_abort: true
        };
      }
        
      const res = await scrapeGridWorker(
        [grid],
        [{ name: category }],
        wid,
        seenPlaceIdsBloom,
        categoryStats,
        { layer2Mode: true, l2NoUniqueCounter, abortL2 },
        page
      );
        
      progress[grid.name] = progress[grid.name] || {};
      progress[grid.name][`cat_${category}_level_L2`] = {
        total_extracted: res.totalExtracted,
        unique: res.uniqueExtracted,
        businesses_found: res.businessesFound,
        categories_with_links: res.categoriesWithLinks,
        false_positives_fixed: res.falsePositivesFixed || 0,
        level: 'L2',
        skipped_due_to_chunks: res.skipped_due_to_chunks || false
      };
      
      // Track consecutive full repeats
      if (res.totalExtracted > 0 && res.uniqueExtracted === 0) {
        // This is a grid with 100% repetition rate
        l2ConsecutiveFullRepeats[category] = (l2ConsecutiveFullRepeats[category] || 0) + 1;
        
        // Check if we've hit the threshold for removal
        if (l2ConsecutiveFullRepeats[category] >= L2_CONSECUTIVE_FULL_REPEATS_LIMIT) {
          console.log(`🚫 Category ${category} has ${L2_CONSECUTIVE_FULL_REPEATS_LIMIT} consecutive grids with 100% repeats - REMOVING`);
          
          // Log this removal to the CSV
          await logExecutionTimeSync(
            _appendToRemovedCategoriesCSVInner, 
            'appendToRemovedCategoriesCSV', 
            grid.name, 
            'L2', 
            {
              category,
              grid: grid.name,
              repeat_count: l2ConsecutiveFullRepeats[category]
            }
          );
          
          // Mark for abort to stop processing more grids for this category
          abortL2[category] = true;
        }
      } else {
        // Reset counter if we find a grid with new unique places
        l2ConsecutiveFullRepeats[category] = 0;
      }
        
      if (res?.skipped_due_to_chunks) {
        l2NoUniqueCounter[category] = (l2NoUniqueCounter[category] || 0) + 1;
        if (l2NoUniqueCounter[category] >= L2_NO_UNIQUE_LIMIT) {
          console.log(`🚫 L2 CHUNK-SKIP ABORT for ${category} — ${L2_NO_UNIQUE_LIMIT} chunk skips`);
          abortL2[category] = true;
        }
      } else {
        l2NoUniqueCounter[category] = 0;
        if (res.totalExtracted >= LAYER2_THRESHOLD && res.businessesFound > 0) {
          passedL2[category].add(grid.name);
        }
      }
      
      queueSaveProgress(progress);
      return res;
    });
    
    // Save progress after completing L2
    await saveProgress(progress);
    
    // Save bloom filter with timing
    await logExecutionTimeSync(
      () => saveSeenPlaceIdsBloom(seenPlaceIdsBloom),
      'saveSeenPlaceIdsBloom.afterL2',
      '',
      ''
    );
  }
  
  // Generate Layer 3 jobs
  const jobsL3 = [];
  await logExecutionTimeSync(
    () => {
      for (const { name: category } of allCategories) {
        const baseGrids = RUN_L3_ONLY
          ? allL1Grids.flatMap(l1 => l1.layer2 || [])
          : SKIP_LAYER2
            ? allL1Grids.filter(g => passedL1[category]?.has(g.name))
            : allL1Grids.flatMap(l1 =>
                (l1.layer2 || []).filter(l2 => passedL2[category]?.has(l2.name))
              );
        
        for (const parentGrid of baseGrids) {
          const l3s = parentGrid.layer3 || [];
          for (const grid of l3s) {
            if (!progress[grid.name]?.[`cat_${category}_level_L3`]) {
              jobsL3.push({ grid: { ...grid, level: 'L3', parent: parentGrid.name }, category });
            }
          }
        }
      }
      // Shuffle the jobs for better distribution
      shuffleInPlace(jobsL3);
      console.log(`📊 Generated ${jobsL3.length} Layer 3 jobs`);
    },
    'generateL3Jobs',
    '',
    ''
  );
  
  if (RUN_L3_ONLY || SKIP_LAYER2 || (!RUN_L2_ONLY && !RUN_L3_ONLY)) {
    console.log(`🧪 Starting Layer 3 with ${jobsL3.length} jobs`);
    await runWithThreadPool(jobsL3, NUM_WORKERS, async ({ grid, category }, wid, page) => {
      // Initialize category-specific abort object if needed
      if (!abortL3[category]) {
        abortL3[category] = {};
      }
      
      if (abortL3[category][grid.parent]) {
        console.log(`⏭️ Skipping ${grid.name} | ${category} due to parent grid abort`);
        progress[grid.name] = progress[grid.name] || {};
        progress[grid.name][`cat_${category}_level_L3`] = {
          total_extracted: 0,
          unique: 0,
          businesses_found: 0,
          categories_with_links: 0,
          level: 'L3',
          skipped_due_to_abort: true
        };
        return {
          grid: grid,
          businessesFound: 0,
          categoriesWithLinks: 0,
          totalExtracted: 0,
          uniqueExtracted: 0,
          durationMin: 0,
          category: category,
          skipped_due_to_abort: true
        };
      }
      
      const res = await scrapeGridWorker(
        [grid],
        [{ name: category }],
        wid,
        seenPlaceIdsBloom,
        categoryStats,
        { layer3Mode: true, l3NoUniqueCounter, abortL3 },
        page
      );
      
      progress[grid.name] = progress[grid.name] || {};
      progress[grid.name][`cat_${category}_level_L3`] = {
        total_extracted: res.totalExtracted,
        unique: res.uniqueExtracted,
        businesses_found: res.businessesFound,
        categories_with_links: res.categoriesWithLinks,
        false_positives_fixed: res.falsePositivesFixed || 0,
        level: 'L3',
        skipped_due_to_chunks: res.skipped_due_to_chunks || false
      };
      
      // Handle early abort for Layer 3 based on parent grid
      if (res.skipped_due_to_chunks || (res.totalExtracted > 0 && res.uniqueExtracted === 0)) {
        l3NoUniqueCounter[category] = (l3NoUniqueCounter[category] || 0) + 1;
        if (l3NoUniqueCounter[category] >= L3_NO_UNIQUE_LIMIT) {
          console.log(`🚫 L3 early abort for ${category} in parent grid ${grid.parent} — ${L3_NO_UNIQUE_LIMIT} grids with no unique results`);
          if (!abortL3[category]) abortL3[category] = {};
          abortL3[category][grid.parent] = true;
        }
      } else {
        l3NoUniqueCounter[category] = 0;
      }
      
      queueSaveProgress(progress);
      return res;
    });
    
    // Save progress after completing L3
    await saveProgress(progress);
  }
  
  // Save bloom filter with timing
  await logExecutionTimeSync(
    () => saveSeenPlaceIdsBloom(seenPlaceIdsBloom),
    'saveSeenPlaceIdsBloom.final',
    '',
    ''
  );
  
  // Close browser with timing
  await closeBrowserPool();
  
  // Generate category summary with timing
  await logExecutionTimeSync(
    () => {
      const catHeader = 'category,grids_ran,grids_successful,total_unique_links,avg_repeat_rate\n';
      const catLines = [catHeader];
      
      for (const [cat, stats] of Object.entries(categoryStats)) {
        const avgRepeat = stats.grids_ran > 0 ? (stats.repeat_rate_sum / stats.grids_ran).toFixed(2) : '0.00';
        catLines.push(`${cat},${stats.grids_ran},${stats.grids_successful},${stats.total_unique_links},${avgRepeat}`);
      }
      
      fs.writeFileSync(CATEGORY_SUMMARY_CSV, catLines.join('\n'));
      console.log(`💾 Saved category summary to ${CATEGORY_SUMMARY_CSV}`);
    },
    'generateCategorySummary',
    '',
    ''
  );
  
  // Generate grid summary with timing
  await logExecutionTimeSync(
    () => {
      const gridHeader = 'grid,level,total_businesses,unique_businesses,categories_with_links,processed_categories\n';
      const gridLines = [gridHeader];
      const gridStats = {};
      
      // Aggregate stats by grid
      for (const [gridName, gridProgress] of Object.entries(progress)) {
        for (const [key, stats] of Object.entries(gridProgress)) {
          if (!key.startsWith('cat_')) continue;
          
          const parts = key.split('_');
          const category = parts[1];
          const level = parts[3];
          
          if (!gridStats[gridName]) {
            gridStats[gridName] = {
              level,
              total_businesses: 0,
              unique_businesses: 0,
              categories_with_links: 0,
              processed_categories: new Set()
            };
          }
          
          gridStats[gridName].total_businesses += stats.total_extracted || 0;
          gridStats[gridName].unique_businesses += stats.unique || 0;
          if ((stats.businesses_found || 0) > 0) {
            gridStats[gridName].categories_with_links++;
          }
          gridStats[gridName].processed_categories.add(category);
        }
      }
      
      // Format grid summary
      for (const [gridName, stats] of Object.entries(gridStats)) {
        gridLines.push(`${gridName},${stats.level},${stats.total_businesses},${stats.unique_businesses},${stats.categories_with_links},${stats.processed_categories.size}`);
      }
      
      fs.writeFileSync(GRID_SUMMARY_CSV, gridLines.join('\n'));
      console.log(`💾 Saved grid summary to ${GRID_SUMMARY_CSV}`);
    },
    'generateGridSummary',
    '',
    ''
  );
  
  // Log final statistics
  console.log(`\n=== 📊 FINAL STATISTICS ===`);
  console.log(`🎯 Total unique places: ${seenPlaceIdsBloom.size}`);
  if (ENABLE_SECONDARY_VERIFICATION) {
    console.log(`🎯 Total exact place IDs: ${exactPlaceIds.size}`);
    console.log(`🎯 Estimated false positive rate: ${((seenPlaceIdsBloom.size - exactPlaceIds.size) / seenPlaceIdsBloom.size * 100).toFixed(2)}%`);
  }
  
  const durationMin = ((Date.now() - startTime) / 60000).toFixed(2);
  console.log(`⏱️ Total execution time: ${durationMin} minutes`);
  
  // Log end of main function
  logExecutionTimeSync(
    () => {},
    'main.end',
    '',
    '',
    {
      durationMin,
      uniquePlaces: seenPlaceIdsBloom.size,
      exactPlaceIds: ENABLE_SECONDARY_VERIFICATION ? exactPlaceIds.size : 'N/A'
    }
  );
}

// === Exit Handling ===
const startTimeGlobal = Date.now();

function handleExit() {
  const durationMin = ((Date.now() - startTimeGlobal) / 60000).toFixed(2);
  console.log(`\n🛑 Interrupted. Total execution time: ${durationMin} minutes`);
  
  logExecutionTimeSync(
    () => {},
    'handleExit',
    '',
    '',
    { durationMin }
  );
  
  closeBrowserPool().then(() => process.exit());
}

process.on('SIGINT', handleExit);
process.on('SIGTERM', handleExit);

main().catch(err => {
  console.error('🚨 Top-level error:', err);
  
  logExecutionTimeSync(
    () => {},
    'main.error',
    '',
    '',
    { error: err.message }
  );
  
  process.exit(1);
});