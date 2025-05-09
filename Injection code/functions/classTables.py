from datetime import date, time, datetime
from typing import Optional, List, Dict
from uuid import UUID
from decimal import Decimal


class Product:
    def __init__(self):
        self.productID: UUID
        self.businessID: Optional[UUID] = None
        self.source: str
        self.description: str
        self.genericDesc: str  # enum
        self.dateAdded: date
        self.category: Optional[str] = None
        self.costItems: Optional[Dict] = None
        self.harvestDate: date
        self.detail: Optional[Dict] = None
        self.comparables: Optional[List] = None
        self.updateDate: date
        self.cost: Optional[Decimal] = None
        self.currency: Optional[str] = None  # enum
        self.relativeCost: Optional[Decimal] = None


class Metrics:
    def __init__(self):
        self.metricsID: UUID
        self.digitalMaturity: Optional[Decimal] = None
        self.businessMaturity: Optional[Decimal] = None
        self.growthProspect: Optional[Decimal] = None
        self.businessCluster: Optional[int] = None
        self.fundamentaScore: Optional[int] = None
        self.updatedDate: Optional[date] = None


class ShoppingCenterBusinesses:
    def __init__(self):
        self.shoppingCenterID: UUID
        self.businessCount: Optional[int] = None
        self.otherInfo: Optional[dict] = None


class ReviewerAffiliates:
    def __init__(self):
        self.reviwerID: UUID  # Note: matches SQL schema's spelling
        self.affiliateID: UUID


class Reviewer:
    def __init__(self):
        self.businessID: UUID
        self.userName: str
        self.bio: Optional[str] = None
        self.followers: Optional[int] = None
        self.following: Optional[int] = None
        self.userProfileLink: Optional[str] = None
        self.userProfilePicture: Optional[str] = None
        self.photoUrls: Optional[Dict] = None
        self.postID: Optional[UUID] = None
        self.email: Optional[str] = None
        self.occupation: Optional[str] = None
        self.persona: Optional[int] = None
        self.age: Optional[int] = None
        self.nickname: Optional[str] = None
        self.firstName: Optional[str] = None
        self.lastName: Optional[str] = None
        self.updateDate: date
        self.homeLocation: Optional[int] = None
        self.homeRegion: Optional[int] = None
        self.locPatterns: Optional[Dict] = None  # Kept as is per SQL schema
        self.associatedURLs: Optional[Dict] = None
        self.assosciatedUsernames: Optional[Dict] = (
            None  # Note: matches SQL schema's spelling
        )
        self.details: Optional[int] = None
        self.ownerOf: Optional[int] = None
        self.affiliateOf: Optional[int] = None
        self.socialID: Optional[UUID] = None
        self.isBusiness: Optional[bool] = None
        self.reviewCount: Optional[int] = None
        self.photoCount:  Optional[int] = None


class Detail:
    def __init__(self):
        self.businessID: UUID
        self.amenities: Optional[List[Dict]] = None   # For the json[] field
        self.links: Optional[Dict] = None
        self.updateDate: Optional[date] = None
        self.previousID: Optional[UUID] = None
        self.about: Optional[str] = None


class Address:
    def __init__(self):
        self.businessID: UUID
        self.addressName: Optional[str] = None
        self.addressNumber: Optional[int] = None
        self.addressStreet: Optional[str] = None
        self.addressUnit: Optional[int] = None
        self.addressLevel: Optional[int] = None
        self.addressDetails: Optional[str] = None
        self.addressPOBox: Optional[str] = None
        self.addressCity: Optional[str] = None
        self.addressProvState: Optional[str] = None
        self.addressRegion: Optional[str] = None
        self.addressNeighborhood: Optional[str] = None
        self.addressPostalCode: Optional[str] = None
        self.addressCountry: Optional[str] = None
        self.addressw3w: Optional[str] = None  # Note: matches SQL schema's case
        self.sources: Optional[str] = None
        self.updateDate: date
        self.addressFull: Optional[str] = None
        self.addressSimple: Optional[str] = None


class Contact:
    def __init__(self):
        self.businessID: Optional[UUID] = None
        self.businessEmail: Optional[str] = None  # Kept as is per SQL schema
        self.businessURL: Optional[str] = None  # Kept as is per SQL schema
        self.socialID: Optional[UUID] = None
        self.phone: Optional[str] = None
        self.email: Optional[str] = None
        self.updateDate: Optional[date] = None


class Business:
    def __init__(self):
        self.businessID: UUID
        self.name: str
        self.gmapsURL: Optional[str] = None
        self.isVerified: Optional[bool] = None
        self.businessStartDate: Optional[date] = None
        self.businessAge: Optional[int] = None
        self.shoppingCenterID: Optional[UUID] = None
        self.isShoppingCenter: Optional[bool] = None
        self.defunct: Optional[int] = None
        self.chain: Optional[int] = False
        self.financials: Optional[Dict] = None
        self.metricsID: Optional[UUID] = None
        self.created: Optional[date] = None
        self.summary: Optional[str] = None
        self.longitude: Optional[Decimal] = None
        self.latitude: Optional[Decimal] = None
        self.updateDate: date
        self.alias: Optional[str] = None
        self.rating: Optional[int] = None
        self.ratingScaled: Optional[int] = None
        self.price: Optional[str] = None
        self.totalReviews: Optional[int] = None
        self.category: Optional[str] = None
        self.permclosed: Optional[bool] = False
        self.locationCount: Optional[int] = None

class ReviewerHistory:
    def __init__(self):
        self.reviewerID: UUID
        self.reviewerName: Optional[str] = None
        self.reviewerProfilePictureURL: Optional[str] = None
        self.reviewPoints: Optional[int] = None
        self.userTagOrContributions: Optional[str] = None
        self.profileLink: Optional[str] = None
        self.businessName: Optional[str] = None
        self.businessAddress: Optional[str] = None
        self.businessRating: Optional[Decimal] = None
        self.ratingTime: Optional[str] = None
        self.reviewText: Optional[str] = None
        self.reviewTags: Optional[List[str]] = None
        self.photos: Optional[List[str]] = None
        self.ownerResponse: Optional[bool] = False
        self.updateDate: Optional[datetime] = None



class Post:
    def __init__(self):
        self.postID: UUID
        self.postLink: Optional[str] = None
        self.caption: str
        self.likes: Optional[int] = None
        self.numComments: Optional[int] = None
        self.createdDate: date
        self.updateDate: date
        self.isBusinessPost: bool
        self.isDeleted: Optional[bool] = None
        self.hashtags: Optional[str] = None
        self.isAffiliate: Optional[bool] = None
        self.postValidity: Optional[Decimal] = None
        self.postQuality: Optional[Decimal] = None
        self.derivedSignals: Optional[Dict] = None
        self.otherMentions: Optional[Dict] = None
        self.level: Optional[int] = None
        self.postViews: Optional[int] = None
        self.postUpvotes: Optional[int] = None
        self.postLength: Optional[int] = None


class Review:
    def __init__(self):
        self.reviewID: UUID
        self.url: Optional[str] = None
        self.platform: str
        self.reviewerID: UUID
        self.ratingRaw: Optional[int] = None
        self.ratingScaled: Optional[int] = None
        self.reviewText: str
        self.ownerResponse: Optional[Dict] = None
        self.upvotes: Optional[int] = None
        self.reviewSentiment: Optional[int] = None
        self.reviewQuality: Optional[int] = None
        self.defunct: Optional[bool] = None
        self.edited: Optional[bool] = None
        self.length: Optional[int] = None
        self.views: Optional[int] = None
        self.isLocal: Optional[bool] = None
        self.derivedSignals: Optional[Dict] = None
        self.parent: Optional[UUID] = None
        self.child: Optional[UUID] = None
        self.updateDate: date
        self.reviewDate: date
        self.reviewViews: Optional[int] = None
        self.reviewLength: Optional[int] = None
        self.reviewValidity: Optional[int] = None
        self.priorVersions: Optional[str] = None  # Kept as is per SQL schema
        self.otherMentions: Optional[Dict] = None  # Kept as is per SQL schema
        self.productID: Optional[UUID] = None


class SupplierCustomer:
    def __init__(self):
        self.Supplier: UUID  # Matches SQL schema's capitalization
        self.Customer: UUID  # Matches SQL schema's capitalization


class Search:
    def __init__(self):
        self.searchID: UUID
        self.topLinks: Optional[str] = None  # Kept as is per SQL schema
        self.query: str
        self.dateOfSearch: date


class Region:
    def __init__(self):
        self.businessID: UUID
        self.name: str
        self.aliases: Optional[List] = None
        self.desc: Optional[str] = None
        self.attr: Optional[Dict] = None
        self.boundary: str  # polygon
        self.size: Optional[Decimal] = None
        self.population: Optional[int] = None
        self.nBusinesses: Optional[int] = None  # Kept as is per SQL schema
        self.flux: Optional[Decimal] = None


class ReviewerOwns:
    def __init__(self):
        self.reviewerID: UUID
        self.ownBusinessID: UUID


class PostProducts:
    def __init__(self):
        self.postID: UUID
        self.productID: UUID


class Social:
    def __init__(self):
        self.socialID: UUID
        self.platform: Optional[str] = None  # enum
        self.url: Optional[int] = None
        self.bio: Optional[int] = None
        self.numPosts: Optional[str] = None
        self.followers: Optional[str] = None
        self.following: Optional[int] = None
        self.created: Optional[date] = None
        self.postID: Optional[UUID] = None
        self.updateDate: Optional[date] = None
        self.metricArrays: Optional[Dict] = None


class OpenedHoursBusy:
    def __init__(self):
        self.businessID: UUID
        self.date: Optional[date] = None
        self.DayOfWeek: Optional[str] = None  # Matches SQL schema's capitalization
        self.Hour: Optional[int] = None  # Matches SQL schema's capitalization
        self.Percent: Optional[int] = None  # Matches SQL schema's capitalization
