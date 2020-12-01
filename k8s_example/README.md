# Jina x k8s

## 🚀 Setup kubectl & minikube on Macbook

### Install kubectl

The kubectl command line tool lets you control Kubernetes clusters. For detailed info, please visit [What is kubectl](https://kubernetes.io/docs/reference/kubectl/overview/).

```python
# install
brew install kubectl
# verify
kubectl version --client
```

### Install minikube

Minikube is local Kubernetes, focusing on making it easy to learn and develop for Kubernetes. For more info, please visit [What is minikube](https://minikube.sigs.k8s.io/docs/start/).

```python
# install
brew install minikube
# verify
minikube version
# start local minikube env
minikube start
# stop local minikube env
minikube stop
```

### Install helm

Helm is a tool that streamlines installing and managing Kubernetes applications. Think of it like Apt/Yum/Homebrew for K8S. For more info, please visit [helm documentation](https://helm.sh/)

```python
# install
brew install helm
# verify
helm version
```

