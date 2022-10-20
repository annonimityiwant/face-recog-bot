# FaceBot

This Repo is uses open source facial detection and recognition technologies to recieve information about people with their faces and be able to search through them by querying with image.

A use case can be reporting faces of criminals from footage and later user their image in other situations and confirm their identity.

## Features

* Reporting faces and evidence Annonymously

* Facial Recognition

* Identity search

## How to deploy 
You can run this bot on any server, I keep it simple.
    
1- Install docker https://docs.docker.com/get-docker/

2- Clone this repo

3- Create a bot in telegram

4- Create a channel in telegram

5- add the bot as an admin to the channel

6- Edit config.conf file with your password and bot token (password is used for initiating the bot and enabling the bot to have the channel id)

7- run following commands

    docker build -t facebot .
after sucessful build

    docker run -t facebot
your bot should be up and running

## Privacy notes

The bot in this repository does not keep any data about the user's ids.

The only database kept in the code for each face

## How to use
* Admin should first initiate the bot with password and send a message from the channel to the bot.

* Users can report faces to the bot using گزارش and following the bot commands and the bot also receives the info about the reporrted person

* Other users can also report additional info about the reported face 

* Users can query faces to bot and see if they were reported before and confirm their identity and take action.


## VERY IMPORTANT NOTE

* Searching for faces among many reported faces is very challenging and the results of the query can have errors.

* ***You are the Ultimate judge, the bot only gives you the information and does not forget any face.***






    
        