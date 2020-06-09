from diagrams import Cluster, Diagram,Edge
from diagrams.programming.framework import React,Graphql
from diagrams.programming.language import Rust
from diagrams.onprem.database import Mongodb
from diagrams.onprem.network import Nginx
from diagrams.onprem.vcs import Gitlab
from diagrams.onprem.vcs import Git
from diagrams.k8s.compute import Job
from diagrams.onprem.container import Docker
from diagrams.k8s.network import Ing
from diagrams.k8s.compute import Deploy
from diagrams.k8s.network import SVC
from diagrams.k8s.compute import RS
from diagrams.k8s.compute import Pod
from diagrams.azure.network import LoadBalancers
from diagrams.k8s.podconfig import CM
from diagrams.k8s.controlplane import API


## Digishop architecture 
with Diagram("digishop specification", show=False,direction="LR"):
    nginx = Nginx("Nginx")
    with Cluster("DigiShop"):
        with Cluster("Mongodb"):
            master = Mongodb("Master")
            slaves = [Mongodb("Slave-1"),Mongodb("Slave-2")]
            master >> Edge(label="pull",style="dashed") >> slaves

        with Cluster("DigiShop Backend"):
            gateway=Graphql("Gateway")
            backend = [
                                Rust("Auth"),
                                Rust("Menu"),
                                Rust("Settings"),
                                Rust("Stats"),
                                Rust("Order")
                                ]
            gateway >>Edge(style="dotted")>> backend
            backend >> master

        with Cluster("DigiShop Frontend"):
            frontend =[React("Admin"),
                                React("Dashboard"),
                                React("Catalogue")]
            nginx >> Edge() << frontend <<Edge(label="GraphQl") >>gateway

    with Cluster("Client Environment") :
        with Cluster("Git repositories"):
            clients = [Git("Aziza Repo"),
                            Git("Bouras Repo"),
                            Git("Sallon Repo")]
            clients << Edge(label="push")  << nginx

        with Cluster("Pipeline"):
            cicd = Gitlab("Gitlab CI/CD")
            cicd <<Edge(label="run") << clients[0] 
            cicd <<Edge(label="run") << clients[1] 
            cicd <<Edge(label="run") << clients[2] 
            test = Job("Test")
            build = Job("Build")
            ship=Docker("Ship")
            deploy=Job("Deploy")
            deploy <<ship<<build<< test<< cicd

        
    with Cluster("Clients kubernetes Cluster") :
        api = API("Api server")
        ingress = Ing("Ingress")
        
        with Cluster("Aziza namespace"):
              deploy1 = Deploy("deployment")
              podaziza=[Pod("Instance1"),
              Pod("Instance2"),
              Pod("Instance3") ]
              svc1 = SVC("service")
              cm1=CM("configMap")
              ingress<<svc1 << deploy1 >> podaziza
              #podaziza[1]<<deploy

        with Cluster("Bouras namespace"):

              deploy2 = Deploy("deployment")
              
              podaziza2=[Pod("Instance1"),
              Pod("Instance2"),
              Pod("Instance3") ]
              cm2=CM("configMap")
              svc2 = SVC("service")
              
              ingress<<svc2 << deploy2 >> podaziza2
              #podaziza2[1]<<deploy

        with Cluster("Sallon namespace"):
              
              deploy3 = Deploy("deployment")
              podaziza3=[Pod("Instance1"),
              Pod("Instance2"),
              Pod("Instance3") ]
              cm3=CM("configMap")
              svc3 = SVC("service")
              ingress<<svc3 << deploy3 >> podaziza3
             #podaziza3[1]<<deploy
        with Cluster("Mongodb"):
            masterc = Mongodb("Master")
            slavesc = [Mongodb("Slave-1"),Mongodb("Slave-2")]
            masterc >> Edge(label="pull",style="dashed") >> slavesc
            podaziza >> masterc
            podaziza2 >> masterc
            podaziza3 >> masterc

    lb = LoadBalancers("Azure lb")
    lb << ingress
    slavesc-Edge(color="#cffffd")-api<< Edge(style="bold",color="red")<< deploy

  
 
  