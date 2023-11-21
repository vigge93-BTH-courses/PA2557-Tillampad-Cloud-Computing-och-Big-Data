docker build -t cwebserver ./CWebServer
docker build -t cworker ./CWorker
docker build -t cfetcher ./CFetcher
docker build -t cdatabaseservice ./CDatabaseService/CDatabaseService

docker rmi $(docker images -f "dangling=true" -q)