#!/usr/bin/python
import docker
import sys
from docker import Client
import json

data_file = open('image-version-dependecy.json', 'r')
data = json.load(data_file)
imageList = (list(data.keys()))
wmRepostrity = ['192.168.1.2:5000']
pullRepo = '192.168.1.2:5000'
cli = Client(base_url='unix://var/run/docker.sock',version="auto")
imageVSbuildMap={}

class image():

    def __init__(self, imName):
        self.imName = imName

    def getVersion(self, imName):
        if imName in data:
            imVersion = data[imName]['version']
            return imVersion

    def getTagName(self, imName):
        if imName in data:
            tagName = 'raju/' + imName
            return tagName

    def getDockerFileLocation(self, imName):
        if imName in data:
            dockerFileLocation = data[imName]['docker-file-location']
            return dockerFileLocation

    def getDependency(self, imName):
        if imName in data:
            dependencies = data[imName]['dependencies']
            return dependencies

    def getRepo(self, imName, repo):
        if imName in data:
            imageRepoUrl = repo + '/' + self.getTagName(imName)
            return imageRepoUrl


class dockerApi():

    def __init__(self, imName):
        self.imName = imName

    def wmDockerPull(self, imName, imTag):
        for line in cli.pull(imName, tag=imTag, stream=True):
            if 'errorDetail' not in line:
                print(line)
            else:
                status = 'False'
                return status
        return line

    def wmDockerPush(self, imName, imtag):
	for line in cli.push(imName, tag=imtag, stream=True):
        	print(json.dumps(json.loads(line), indent=4))

    def wmDockerBuild(self, imName, dockerFileLocation):
        for line in cli.build(path=dockerFileLocation, tag=imName, stream=True, rm=True):
            res = json.dumps(json.loads(line), indent=4)
            print(res)

    def wmDockerTag(self, imName, imTag, repoName):
	cli.tag(image=imName, tag=imTag, repository=repoName, force=True)

    def wmDockerDel(imName):
        cli.remove_image(imName)


#TODO: declare a imageVSbuildMap map of image vs build status and populate
def buildImage(imageName):
    c1 = image(imageName)
    imageDockerFileLocation = data[imageName]['docker-file-location']
    imageVersion = c1.getVersion(imageName)
    imageRepoUrl = c1.getRepo(imageName, pullRepo)
    imageWithTag = c1.getTagName(imageName)
    c2 = dockerApi(imageName)
    try:
        imageStatus = c2.wmDockerPull(imageRepoUrl, imageVersion)
    except docker.errors.NotFound:
        pass
    if ((imageStatus != 'False') and (imageName in imageVSbuildMap and imageVSbuildMap[imageName] is True)):
        c2.wmDockerTag(imageRepoUrl + ':' + imageVersion, imageVersion, imageWithTag)
	print('Already Build skipping' + ' ' + imageName)
        return
    else:
        dependantImagesList = data[imageName]['dependencies']
        if dependantImagesList:
            depenantImagesListLength = len(dependantImagesList)
            rLen = list(range(depenantImagesListLength))
            for i in rLen:
                dependantImage = dependantImagesList[i]
                buildImage(dependantImage)
        c2.wmDockerBuild(imageWithTag + ':' + imageVersion, imageDockerFileLocation)
	for repo in wmRepostrity:
		imagePushUrl=c1.getRepo(imageName, repo)
	        c2.wmDockerTag(imageWithTag + ':' + imageVersion, imageVersion, imagePushUrl)
        	c2.wmDockerPush(imagePushUrl, imageVersion)
	imageVSbuildMap[imageName] = True
#TODO populate the map imageVSbuildMap


def main():
    if len(sys.argv) != 2:
        print("This script requires imageName as argument...")
    elif sys.argv[1] == "All":
        for image in imageList:
            buildImage(image)
    elif sys.argv[1] in imageList:
        buildImage(sys.argv[1])
    else:
        print("Wrong argument....!")
        sys.exit()

if __name__ == "__main__":
    main()
