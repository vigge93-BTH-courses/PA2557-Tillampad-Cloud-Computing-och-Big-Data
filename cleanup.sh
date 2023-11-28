kubectl delete --cascade='foreground' -f assignment1.yml -l app=cworker --grace-period=30
kubectl delete --cascade='foreground' -f assignment1.yml -l app=cfetcher--grace-period=30
kubectl delete --cascade='foreground' -f assignment1.yml --grace-period=30
for file in tmp
do
  kubectl delete --cascade='foreground' -f $file
done
kubectl delete --cascade='foreground' -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml" --grace-period=30
kubectl delete pvc --all
rm tmp/shard-*.yml
rmdir tmp