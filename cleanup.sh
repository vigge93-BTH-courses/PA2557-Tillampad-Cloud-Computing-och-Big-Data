kubectl delete --cascade='foreground' -f assignment1.yml
kubectl delete --cascade='foreground' -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"
kubectl delete pvc --all