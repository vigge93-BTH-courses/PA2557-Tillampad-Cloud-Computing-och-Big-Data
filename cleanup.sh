kubectl delete --cascade='foreground' -f assignment1.yml --grace-period=30
kubectl delete --cascade='foreground' -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml" --grace-period=30
kubectl delete pvc --all
