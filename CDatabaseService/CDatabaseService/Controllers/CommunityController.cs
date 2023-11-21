using Microsoft.AspNetCore.Mvc;

namespace CDatabaseService.Controllers
{
    [ApiController]
    [Route("/communities")]
    public class CommunityController : ControllerBase
    {
        private readonly ILogger<CommunityController> _logger;
        private readonly CommunityService _communityService;

        public CommunityController(ILogger<CommunityController> logger, CommunityService communityService)
        {
            _logger = logger;
            _communityService = communityService;
        }

        [HttpGet(Name = "GetCommunities")]
        public async Task<IEnumerable<Community>> Get()
        {
            return await _communityService.GetAsync();
        }

        [HttpPost(Name = "PostCommunities")]
        public async Task<IActionResult> Post(Community community)
        {
            await _communityService.CreateAsync(community);
            return new OkResult();
        }
    }
}