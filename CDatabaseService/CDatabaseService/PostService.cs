using Microsoft.Extensions.Options;
using MongoDB.Driver;

namespace CDatabaseService
{
    public class PostService
    {

        private readonly IMongoCollection<Post> _postsCollection;

        public PostService(
            IOptionsMonitor<DatabaseSettings> options)
        {
            var postServiceDatabaseSettings = options.Get("PostDB");
            var mongoClient = new MongoClient(
                $@"mongodb://{postServiceDatabaseSettings.ConnectionString}");

            var mongoDatabase = mongoClient.GetDatabase(
                postServiceDatabaseSettings.DatabaseName);

            _postsCollection = mongoDatabase.GetCollection<Post>(
                postServiceDatabaseSettings.CollectionName);
        }

        public async Task<List<Post>> GetAsync() =>
            await _postsCollection.Find(_ => true).ToListAsync();

        public async Task<List<Post>> GetAsync(long communityId, string instanceUrl) =>
            await _postsCollection.Find(x => x.CommunityId == communityId && x.InstanceUrl == instanceUrl).ToListAsync();

        public async Task CreateAsync(Post newCommunity) =>
            await _postsCollection.InsertOneAsync(newCommunity);

        public async Task UpdateAsync(string id, Post updatedCommunity) =>
            await _postsCollection.ReplaceOneAsync(x => x.Id == id, updatedCommunity);

        public async Task RemoveAsync(long communityId, string instanceUrl) =>
            await _postsCollection.DeleteManyAsync(x => x.CommunityId == communityId && x.InstanceUrl == instanceUrl);
    }
}