using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Bson;
using System.ComponentModel.DataAnnotations;
using System;

namespace CDatabaseService
{
    [BsonIgnoreExtraElements]
    public class Post
    {
        [BsonId]
        [BsonRepresentation(BsonType.ObjectId)]
        public string? Id { get; set; }
        [BsonElement("instance_url")]
        public string? InstanceUrl { get; set; }
        [BsonElement("community_id")]
        public long? CommunityId { get; set; }
        [BsonElement("post_id")]
        public long? PostId { get; set; }
        [BsonElement("name")]
        public string? Name { get; set; }
        [BsonElement("url")]
        public string? Url { get; set; }
        [BsonElement("body")]
        public string? Body {get; set; }
        [BsonElement("removed")]
        public bool? Removed {get; set; }
        [BsonElement("deleted")]
        public bool? Deleted { get; set; }
        [BsonElement("nsfw")]
        public bool? Nsfw { get; set; }
        [BsonElement("published")]
        public DateTime? Published { get; set; }
        [BsonElement("embed_title")]
        public string? EmbedTitle {get; set; }
        [BsonElement("embed_description")]
        public string? EmbedDescription { get; set; }
        [BsonElement("thumbnail_url")]
        public string? ThumbnailUrl { get; set; }
        [BsonElement("counts")]
        public Counts? Counts { get; set; }
    }

    [BsonIgnoreExtraElements]
    public class Counts
    {
        [BsonElement("comments")]
        public long? Comments { get; set; }
        [BsonElement("score")]
        public long? Score { get; set; }
        [BsonElement("upvotes")]
        public long? Upvotes { get; set; }
        [BsonElement("downvotes")]
        public long? Downvotes { get; set; }
        [BsonElement("published")]
        public DateTime? Published { get; set; }
    }
}
