using Microsoft.AspNetCore.Mvc;
using System.Runtime.CompilerServices;

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

        [HttpDelete(Name = "DeleteCommunities")]
        public async Task<IActionResult> Delete(string id)
        {
            var community = await _communityService.GetAsync(id);
            if (community == null)
            {
                new NotFoundResult();
            }
            await _communityService.RemoveAsync(id);
            return new OkObjectResult(community);
        }
    }
}