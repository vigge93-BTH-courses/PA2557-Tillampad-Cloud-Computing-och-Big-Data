using Microsoft.AspNetCore.Mvc;

namespace CDatabaseService.Controllers
{
    [ApiController]
    [Route("/posts")]
    public class PostController : ControllerBase
    {
        private readonly ILogger<PostController> _logger;
        private readonly PostService _postService;
        private readonly CommunityService _communityService;

        public PostController(ILogger<PostController> logger, PostService postService, CommunityService communityService)
        {
            _logger = logger;
            _postService = postService;
            _communityService = communityService;
        }

        [HttpGet(Name = "GetPosts")]
        public async Task<IEnumerable<Post>> Get(string communityObjId)
        {
            var community = await _communityService.GetAsync(communityObjId);
            return await _postService.GetAsync(community?.CommunityId ?? -1, community?.InstanceUrl ?? "");
        }

        [HttpDelete(Name = "DeletePosts")]
        public async Task<IActionResult> Delete(long communityId, string instanceUrl)
        {
            await _postService.RemoveAsync(communityId, instanceUrl);
            return new OkResult();
        }
    }
}