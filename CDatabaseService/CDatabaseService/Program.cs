using CDatabaseService;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.Configure<DatabaseSettings>("CommunityDB",
    builder.Configuration.GetSection("CDatabaseService").GetSection("CommunityDB"));
builder.Services.Configure<DatabaseSettings>("PostDB",
    builder.Configuration.GetSection("CDatabaseService").GetSection("PostDB"));
builder.Services.AddSingleton<CommunityService>();
builder.Services.AddSingleton<PostService>();
builder.Services.AddControllers();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();
