using Microsoft.AspNetCore.Mvc;

namespace CDatabaseService.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class DatabaseServiceController : ControllerBase
    {
        private readonly ILogger<DatabaseServiceController> _logger;
        private readonly CommunityService _communityService;

        public DatabaseServiceController(ILogger<DatabaseServiceController> logger, CommunityService communityService)
        {
            _logger = logger;
            _communityService = communityService;
        }

        [HttpGet("/communities", Name = "GetCommunities")]
        public async Task<IEnumerable<Community>> Get()
        {
            return await _communityService.GetAsync();
        }
    }
}