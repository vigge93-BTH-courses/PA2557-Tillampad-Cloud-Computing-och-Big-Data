docker build -t cwebserver ./CWebServer
docker build -t cworker ./CWorker
docker build -t cfetcher ./CFetcher
docker build -t cdatabaseservice ./CDatabaseService/CDatabaseService

docker tag cwebserver:latest viar19/pa2577-a1:cwebserver
docker tag cworker:latest viar19/pa2577-a1:cworker
docker tag cfetcher:latest viar19/pa2577-a1:cfetcher
docker tag cdatabaseservice:latest viar19/pa2577-a1:cdatabaseservice

docker push viar19/pa2577-a1:cwebserver
docker push viar19/pa2577-a1:cworker
docker push viar19/pa2577-a1:cfetcher
docker push viar19/pa2577-a1:cdatabaseservice

docker rmi $(docker images -f "dangling=true" -q)