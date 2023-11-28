using Microsoft.Extensions.Options;
using MongoDB.Driver;

namespace CDatabaseService
{
    public class CommunityService
    {

        private readonly IMongoCollection<Community> _communitiesCollection;

        public CommunityService(
            IOptionsMonitor<DatabaseSettings> options)
        {
            var communityServiceDatabaseSettings = options.Get("CommunityDB");
            var mongoClient = new MongoClient(
                $@"mongodb://{communityServiceDatabaseSettings.ConnectionString}/?directConnection=false");

            var mongoDatabase = mongoClient.GetDatabase(
                communityServiceDatabaseSettings.DatabaseName);

            _communitiesCollection = mongoDatabase.GetCollection<Community>(
                communityServiceDatabaseSettings.CollectionName);
        }

        public async Task<List<Community>> GetAsync() =>
            await _communitiesCollection.Find(_ => true).ToListAsync();

        public async Task<Community?> GetAsync(string id) =>
            await _communitiesCollection.Find(x => x.Id == id).FirstOrDefaultAsync();

        public async Task<ReplaceOneResult> CreateAsync(Community newCommunity)
        {
            var builder = Builders<Community>.Filter;
            var filter = builder.Eq(community => community.InstanceUrl, newCommunity.InstanceUrl)
                        & builder.Eq(community => community.Name, newCommunity.Name);
            return await _communitiesCollection.ReplaceOneAsync(filter, newCommunity, new ReplaceOptions { IsUpsert = true });
        }

        public async Task UpdateAsync(string id, Community updatedCommunity) =>
            await _communitiesCollection.ReplaceOneAsync(x => x.Id == id, updatedCommunity);

        public async Task RemoveAsync(string id) =>
            await _communitiesCollection.DeleteOneAsync(x => x.Id == id);
    }
}