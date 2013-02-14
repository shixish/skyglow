Skyglow python project
=========
I wrote this code during a summer internship with Textron Systems in Kehei, Maui (Hawaii) as part of the Akamai summer internship program.

Purpose
-------
This code was written to index a large volume of raw sensor-images (many terabytes), pull out useful metadata, then produce data exports such as various image outputs using different filters and formats, video, and pdf reports. The system creates a SQLite database to store the necessary metadata.

The data comes from an automated imaging device that basically takes pictures of the night sky. The images are stored in a type of raw format that just stores the brightness values measured by their sensors. The images are tagged with several attributes which indicate the direction the camera was pointing when the image was taken, as well as various other stats. The camera was actually set up to take a full 60 frames per second, which in my opinion was way overkill considdering they were mostly just pictures of clouds. In order to cut down on this, I did a sampling of the actual data, and just pulled out keyframes, 1 per second.

Several steps were taken to fix erroneous metadata. The sensors which produce these raw image files often produce random spikes in the orientation data which can be detected and eliminated. My approach was to approximate the appropriate values by looking at the metadata of the surrounding measurements, and basically taking an average.

It was also a challenge to produce the desired image outputs. The sensor-image data came packaged in a proprietary format, and needed to first be converted to something more usable. The sensor-image data is basically just a matrix of brightness values of arbitrary scale. The naive approach was to simply scale each value between 0 and 255, 0 meaning black, 255 representing white. I initially did so by first finding the smallest and largest values in the matrix, then scale by that. It quickly became apparent that this would not work. These sensors were sometimes faulty; producing wild spikes as well as dead pixels, so the highest value and lowest value gave a very poor estimation of where the majority of the values lay. The image would come out looking oversaturated, or just black.

I came up with a new approach to this problem. My goal was to produce images which will contain the most visible information and detail. The system first gets the average of all of the points, then calculates the standard deviation. I then simply scaled the values by about 2 or 3 standard deviations above and below the average value. This produces some very nice results.

I found that this technique worked well for individual images, and would produce an image that looked good on its own, but I decided it would make sense if a set of images used the same scaling, allowing you to reasonably compare between adjacent images. Using the database I had built up, I was able to pull an average and standard deviation for a whole set of images, then use those values to scale the whole set of images the same way.

Outcomes
---
My code built on some python code that was written to do the same thing. The code was poorly structured, very inefficient, and contained bugs that I was instructed to fix. I rewrote most of this code. I primarily kept some of the routines that applied filters to resultant images. I argued that the system would benefit from an SQLite database, my advisor hesitantly accepted but was pleasantly surprised when I pulled through. Their original system built up giant datastructure that was then stored in a file using 'pickle'. Not so good. I was told that the system was thrown together as a kind of kludge to simply get the job done quickly for their client.

I think I worked on this code for about a Month, and was able to produce a pretty substantial product. This was the first time I had ever touched the Python programming language, and this was also my first time using the Git version control software. To make matters worse, I couldn't get internet access for the first week or so, because I wasn't able to access their network without the proper clearance (long story). I basically spent this time learning the language by reading through their code.

My system turned out to be significantly more efficient then their original code. My system produced higher quality outputs, and ran in significantly less time. My system could process a 2TB harddrive in a couple hours, where the old system used to take all night. The database was stored with the data, so once the index was built, you wouldn't have to rebuild it. I improved the outputs by reducing the errors in the data, and the image output looked a lot better due to my scaling techniques.

I checked in with them a few months later, and they said they were still pleased with my work, and they had continued to use it, and build upon it. One of my advisors, Peter Konohia wrote me a letter of recommendation for my work, see: AndrewLetterOfRecomendation.pdf

Files
---
- dataGraph.png - shows a graph of one image. Each line illustrates one row of pixels across the image. Spikes indicate either a bright star, or an erroneous reading. I think the blue bars incidate 1 std from the average, and I think the red bars are 3 (not sure, I don't remember :) I used these types of graphs to help figure out the image scaling.

- dirtyPositions.png - shows a graph of the position metadata. The hight is simply the summation of two position values (I believe it was azimuth and altitude), the horizontal axis represents every image in the database index, organized by time. The tall spikes upward indicate the "slewing frames". The slewing frames are when the camera was moving, to indicate this, the system simply sets the position values to some arbitrary large value. Silly as it sounds, they kept the camera rolling as the robotic arm changed the orientation of the camera, so there are all of these blurred images of smeared stars, etc. I can't imagine they would be useful to the researchers, but I found these frames to be far more interesting to look at. The short sections that look like little steps indicate a section of time where the camera was still, watching the same spot for a few seconds. The blue lines illustrate the corrected values, and the green lines indicate the original values. The green spikes are indicative of an error in the position values (the green line is obscured by the blue line when there are no errors).

- AndrewLetterOfRecomendation.pdf - Letter of recommendation from Peter Konohia, Textron Defense Systems.

