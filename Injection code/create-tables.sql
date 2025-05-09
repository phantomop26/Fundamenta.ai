
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

CREATE SEQUENCE IF NOT EXISTS reviewer_affiliate_id_seq;

CREATE TABLE IF NOT EXISTS ReviewerAffiliates (
  "reviwerID" uuid NOT NULL,
  "affiliateID" uuid NOT NULL,
  PRIMARY KEY ("reviwerID", "affiliateID")
);

CREATE TABLE IF NOT EXISTS Reviewer (
  "reviewerID" uuid NOT NULL PRIMARY KEY,
  "userName" text NOT NULL,
  "bio" text,
  "followers" integer,
  "following" integer,
  "userProfileLink" text,
  "userProfilePicture" text,
  "photoUrls" json,
  "postID" uuid,
  "email" text,
  "occupation" text,
  "persona" bigint,
  "age" smallint,
  "nickname" text,
  "firstName" text,
  "lastName" text,
  "updateDate" date NOT NULL,
  "homeLocation" bigint,
  "homeRegion" bigint,
  "locPatterns" json,
  "associatedURLs" json,
  "assosciatedUsernames" json,
  "details" bigint,
  "ownerOf" bigint,
  "affiliateOf" bigint,
  "socialID" uuid,
  "isBusiness" boolean,
  "reviewCount" bigint,
  "photoCount" bigint
);

COMMENT ON TABLE Reviewer IS 'isBusiness default False';

CREATE TABLE IF NOT EXISTS ReviewerOwns (
  "reviewerID" uuid NOT NULL,
  "ownBusinessID" uuid NOT NULL,
  PRIMARY KEY ("reviewerID", "ownBusinessID")
);

CREATE TABLE IF NOT EXISTS ShoppingCenterBusinesses (
  "shoppingCenterID" uuid NOT NULL PRIMARY KEY, 
  "businessCount" bigint,
  "otherInfo" json
);

CREATE TABLE IF NOT EXISTS Detail (
  "businessID" uuid NOT NULL PRIMARY KEY,
  "amenities" json,
  "links" json,
  "updateDate" date,
  "previousID" uuid,
  "about" text
);

COMMENT ON TABLE Detail IS 'This should be in the busiess?';

CREATE TABLE IF NOT EXISTS Region (
  "businessID" uuid NOT NULL PRIMARY KEY,
  "name" text NOT NULL,
  "aliases" text[],
  "desc" text,
  "attr" json,
  "boundary" polygon NOT NULL,
  "size" decimal,
  "population" bigint,
  "nBusinesses" bigint,
  "flux" decimal
);

COMMENT ON TABLE Region IS 'size, pop, n_business default 0';

CREATE TABLE IF NOT EXISTS Contact (
  "businessID" uuid PRIMARY KEY,
  "businessEmail" text,
  "businessURL" text,
  "socialID" uuid,
  "phone" text,
  "email" text,
  "updateDate" date
);

CREATE TABLE IF NOT EXISTS PostProducts (
  "postID" uuid NOT NULL,
  "productID" uuid NOT NULL,
  PRIMARY KEY ("postID", "productID")
);

CREATE TABLE IF NOT EXISTS Social (
  "socialID" uuid NOT NULL PRIMARY KEY,
  "platform" text,
  "url" bigint,
  "bio" bigint,
  "numPosts" text,
  "followers" varchar(500),
  "following" bigint,
  "created" date,
  "postID" uuid,
  "updateDate" date,
  "metricArrays" json
);

CREATE TABLE IF NOT EXISTS Review (
  "reviewID" uuid NOT NULL PRIMARY KEY,
  "businessID" uuid NOT NULL,
  "url" text,
  "platform" text NOT NULL,
  "reviewerID" uuid NOT NULL,
  "ratingRaw" bigint,
  "ratingScaled" bigintow,
  "reviewText" text NOT NULL,
  "ownerResponse" json,
  "upvotes" smallint,
  "reviewSentiment" bigint,
  "reviewQuality" bigint,
  "defunct" boolean,
  "edited" boolean,
  "length" bigint,
  "views" bigint,
  "isLocal" boolean,
  "derivedSignals" json,
  "parent" uuid,
  "child" uuid,
  "updateDate" date NOT NULL,
  "reviewDate" date NOT NULL,
  "reviewViews" bigint,
  "reviewLength" bigint,
  "reviewValidity" bigint,
  "priorVersions" text,
  "otherMentions" json,
  "productID" uuid 
);

COMMENT ON TABLE Review IS 'platform should not be a social. review length default 0. defunct, is_local default to False';
COMMENT ON COLUMN Review.defunct IS 'I dont know what this means';

CREATE TABLE IF NOT EXISTS Post (
  "postID" uuid NOT NULL PRIMARY KEY,
  "postLink" text,
  "caption" text,
  "likes" smallint,
  "numComments" smallint,
  "createdDate" date NOT NULL,
  "updateDate" date NOT NULL,
  "isBusinessPost" boolean NOT NULL,
  "isDeleted" boolean,
  "hashtags" text,
  "isAffiliate" boolean,
  "postValidity" decimal,
  "postQuality" decimal,
  "derivedSignals" json,
  "otherMentions" json,
  "level" bigint,
  "postViews" bigint,
  "postUpvotes" bigint,
  "postLength" bigint
);

COMMENT ON TABLE Post IS 'level, views, upvotes, length, default 0. isDeleted default False';

CREATE TABLE IF NOT EXISTS Business (
  "businessID" uuid NOT NULL PRIMARY KEY,
  "gmapsURL" text,
  "name" text NOT NULL,
  "isVerified" boolean,
  "businessStartDate" date,
  "businessAge" bigint,
  "shoppingCenterID" uuid,
  "isShoppingCenter" boolean,
  "defunct" bigint,
  "chain" boolean,
  "financials" json,
  "metricsID" uuid,
  "created" date,
  "summary" text,
  "longitude" decimal ,
  "latitude" decimal,
  "updateDate" date NOT NULL,
  "alias" text,
  "rating" decimal,
  "ratingScaled" decimal,
  "price" text,
  "totalReviews" bigint,
  "category" text,
  "permclosed" boolean,
  "locationCount" bigint,
   categoryGeneral text
);

COMMENT ON TABLE Business IS 'defunct, chain default false';

CREATE TABLE IF NOT EXISTS Search (
  "searchID" uuid NOT NULL PRIMARY KEY,
  "topLinks" text,
  "query" text NOT NULL,
  "dateOfSearch" date NOT NULL
);

CREATE TABLE IF NOT EXISTS SupplierCustomer (
  "Supplier" uuid NOT NULL,
  "Customer" uuid NOT NULL,
  PRIMARY KEY ("Supplier", "Customer")
);

CREATE TABLE IF NOT EXISTS Product (
  "productID" uuid NOT NULL PRIMARY KEY,
  "businessID" uuid,
  "source" text NOT NULL,
  "description" text NOT NULL,
  "genericDesc" text NOT NULL,
  "dateAdded" date NOT NULL,
  "category" text,
  "costItems" json,
  "harvestDate" timestamp with time zone NOT NULL,
  "detail" json,
  "comparables" text[],
  "updateDate" date NOT NULL,
  "cost" decimal,
  "currency" text,
  "relativeCost" decimal
);

CREATE TABLE IF NOT EXISTS ReviewScore (
    reviewID UUID PRIMARY KEY,
    reviewText TEXT,
    category VARCHAR(255),
    buyAgain INT,
    csat INT,
    serviceSpeed INT,
    quality INT,
    convenience INT,
    cleanliness INT,
    localConvenience INT,
    locationConvenience INT,
    spaceCapacity INT,
    noiseLevel INT,
    trustworthiness INT,
    competitionComparison INT,
    trendiness INT,
    tags TEXT[],
    CONSTRAINT fk_review
        FOREIGN KEY (reviewID)
        REFERENCES Review("reviewID")
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Metrics (
  "metricsID" uuid NOT NULL PRIMARY KEY,
  "digitalMaturity" decimal,
  "businessMaturity" decimal,
  "growthProspect" decimal,
  "businessCluster" bigint,
  "fundamentaScore" bigint,
  "updatedDate" date
);

CREATE TABLE IF NOT EXISTS Address (
  "businessID" uuid NOT NULL PRIMARY KEY,
  "addressName" text,
  "addressNumber" integer,
  "addressStreet" text,
  "addressUnit" integer,
  "addressLevel" integer,
  "addressDetails" text,
  "addressPOBox" text,
  "addressCity" text,
  "addressProvState" text,
  "addressRegion" text,
  "addressNeighborhood" text,
  "addressPostalCode" text,
  "addressCountry" text,
  "addressw3w" text,
  "sources" text,
  "updateDate" date NOT NULL,
  "addressFull" text,
  "addressSimple" text
);

CREATE TABLE IF NOT EXISTS openedHoursBusy (
  "businessID" uuid NOT NULL,
  "date" date,
  "dayOfWeek" text,
  "hour" int,
  "percent" bigint
);

ALTER TABLE Address ADD CONSTRAINT Business_addressID_fk FOREIGN KEY ("businessID") REFERENCES Business ("businessID");
ALTER TABLE Detail ADD CONSTRAINT Business_details_fk FOREIGN KEY ("businessID") REFERENCES Business ("businessID");
ALTER TABLE Business ADD CONSTRAINT Business_fundamentaMetrics_fk FOREIGN KEY ("metricsID") REFERENCES Metrics ("metricsID");
ALTER TABLE Region ADD CONSTRAINT Business_regionID_fk FOREIGN KEY ("businessID") REFERENCES Business ("businessID");
ALTER TABLE Review ADD CONSTRAINT Business_reviews_fk FOREIGN KEY ("businessID") REFERENCES Business ("businessID");
ALTER TABLE Business ADD CONSTRAINT Business_shoppingCenterID_fk FOREIGN KEY ("shoppingCenterID") REFERENCES ShoppingCenterBusinesses ("shoppingCenterID");
ALTER TABLE Contact ADD CONSTRAINT Business_contactID_fk FOREIGN KEY ("businessID") REFERENCES Business ("businessID");


ALTER TABLE Contact ADD CONSTRAINT Contact_SocialID_fk FOREIGN KEY ("socialID") REFERENCES Social ("socialID");
ALTER TABLE openedHoursBusy ADD CONSTRAINT openedHoursBusy_detailsID_fk FOREIGN KEY ("businessID") REFERENCES Detail ("businessID");
ALTER TABLE PostProducts ADD CONSTRAINT PostProducts_postID_fk FOREIGN KEY ("postID") REFERENCES Post ("postID");
ALTER TABLE PostProducts ADD CONSTRAINT PostProducts_productID_fk FOREIGN KEY ("productID") REFERENCES Product ("productID");
ALTER TABLE Product ADD CONSTRAINT Product_businessID_fk FOREIGN KEY ("businessID") REFERENCES Business ("businessID");
ALTER TABLE Review ADD CONSTRAINT Review_product_fk FOREIGN KEY ("productID") REFERENCES Product ("productID");
ALTER TABLE Review ADD CONSTRAINT Review_userID_fk FOREIGN KEY ("reviewerID") REFERENCES Reviewer ("reviewerID");
ALTER TABLE ReviewerAffiliates ADD CONSTRAINT ReviewerAffiliates_affiliateID_fk FOREIGN KEY ("affiliateID") REFERENCES Business ("businessID");
ALTER TABLE ReviewerAffiliates ADD CONSTRAINT ReviewerAffiliates_reviwerID_fk FOREIGN KEY ("reviwerID") REFERENCES Reviewer ("reviewerID");
ALTER TABLE ReviewerOwns ADD CONSTRAINT ReviewerOwns_ownBusinessID_fk FOREIGN KEY ("ownBusinessID") REFERENCES Business ("businessID");
ALTER TABLE ReviewerOwns ADD CONSTRAINT ReviewerOwns_reviewerID_fk FOREIGN KEY ("reviewerID") REFERENCES Reviewer ("reviewerID");
ALTER TABLE Social ADD CONSTRAINT Social_postID_fk FOREIGN KEY ("postID") REFERENCES Post ("postID");
ALTER TABLE SupplierCustomer ADD CONSTRAINT SupplierCustomer_Customer_fk FOREIGN KEY ("Customer") REFERENCES Business ("businessID");
ALTER TABLE SupplierCustomer ADD CONSTRAINT SupplierCustomer_Supplier_fk FOREIGN KEY ("Supplier") REFERENCES Business ("businessID");
ALTER TABLE Reviewer ADD CONSTRAINT User_socialID_fk FOREIGN KEY ("socialID") REFERENCES Social ("socialID");