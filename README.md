# AuctionIO-concurrent-app
AuctionIO is a program that simulates a client-host relationship.
Hosts are working concurrently to each other and to the main root of the app.
The selection of a client that can send its file to a free host is controlled by an equation:

![\Large coefficient=\frac{t}{c}+\log_{\frac{1}{2}}\frac{v}{c}](https://latex.codecogs.com/svg.latex?\Large&space;coefficient=\frac{t}{c}+\log_{\frac{1}{2}}\frac{v}{c})

Where:
c - number of clients in queue
t - time that client spend in queue
v - volume of the file client want to upload
Based on the coefficient, clients are selected that can send a file to the host at the same
time it must be the smallest file in the file pack.
