# hostio
okey, I hated coolify and other hosting tools, always seemed unneceseraly bloated and felt like they didnt communicate me on inner workings enough (like being able to acces git repo), so I wanna make my own :D

/src/client is the client side of hostio, it is a CLI tool that allows you to manage your hostio server and deploy your apps to it.
/src/server is the server side of hostio, it is a web server that allows you to manage your hostio server and deploy your apps to it.

/test a simple bun app to test it - goal is to make working https, subdomain resolver and docker containerization all managed by hostio / just realized its gitinored lol :D

# done:
1. uploading projects
2. listing projects

# fuck me:
1. So my stupid head thought it would be epic to make the things like super easy to use docker compose only - project equals resource which is one docker compose, but now I wanna add support for infra of type like next.js + postgres lol
2. My plan is as follows - since I have managed to make the compose working (I just realized I have to merge the branches now since I didnt pull it gg) I will now do the reverse proxy thingy - https + dns resolver in golang, only after that I will add the project:resources based type of hosting - btw you should only need docker.
3. [KIRI](https://runkiri.com/) SUPPORT

 docker compose --progress json --ansi never up --build
