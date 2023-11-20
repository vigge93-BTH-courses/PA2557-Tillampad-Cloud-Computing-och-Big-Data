using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace CDatabaseService
{
    public class Community
    {
        [BsonId]
        [BsonRepresentation(BsonType.ObjectId)]
        public string? Id{ get; set; }
        [BsonElement("community_id")]
        public long CommunityId { get; set; }
        [BsonElement("name")]
        public string Name { get; set; } = null!;
        [BsonElement("title")]
        public string? Title { get; set; }
        [BsonElement("description")]
        public string? Description { get; set; }
        [BsonElement("removed")]
        public bool Removed { get; set; }
        [BsonElement("nsfw")]
        public bool Nsfw { get; set; }
        [BsonElement("icon")]
        public Uri? Icon { get; set; }
        [BsonElement("banner")]
        public Uri? Banner { get; set; }
        [BsonElement("last_update")]
        public DateTime LastUpdate { get; set; }
    }
}