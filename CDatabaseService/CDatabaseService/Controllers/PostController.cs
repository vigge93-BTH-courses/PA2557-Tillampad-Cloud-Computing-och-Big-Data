using Microsoft.AspNetCore.Mvc;

namespace CDatabaseService.Controllers
{
    [ApiController]
    [Route("/posts")]
    public class PostController : ControllerBase
    {
        private readonly ILogger<PostController> _logger;
        private readonly PostService _postService;

        public PostController(ILogger<PostController> logger, PostService postService)
        {
            _logger = logger;
            _postService = postService;
        }

        [HttpGet(Name = "GetPosts")]
        public async Task<IEnumerable<Post>> Get(long communityId)
        {
            return await _postService.GetAsync(communityId);
        }
    }
}