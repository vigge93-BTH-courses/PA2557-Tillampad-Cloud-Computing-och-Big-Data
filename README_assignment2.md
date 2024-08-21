# Question 1
I am not able to process the entire data set. There are several things that limit the number of files processed, and at most I managed to process about 25,500 files. One of the limitations I ran into was that the consumer would sometimes freeze up and refuse to process any more files. There was no consistent point at which this would happen, but instead varied across runs. After some light debugging, my conclusion is that Node.js simply runs out of available memory. This is based on the error message "FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed" that was recieved for one run. This is further corroborated by the fact that increasing the memory limit somewhat alleviated the problem.

There was also a weird problem where the file sent from the producer would sometimes not have data or filepath, which would result in the program crashing. This was fixed with a simple check for if the data or filepath is undefined.

Another problem was the amount of time it took to process the files. The more files got processed, the longer the files took to process. This would have been a larger problem if the program managed to run past the 25,500 mentioned above.

Also, using a more performance oriented programming language, such as Rust, C/C++, Go, etc. could significantly reduce the processing time, with the tradeoff being longer development time.
![Relevant XKCD](https://imgs.xkcd.com/comics/is_it_worth_the_time_2x.png)

# Question 2
One way to reduce the average number of comparison is to return early from the comparison if two lines don't match, since if any two lines don't match, you don't need to check the rest. You could also probably do something with hashmaps to speed up the comparisons, i.e. if we keep a hashmap the first line of code in each chunk, mapped to the chunk, we can then hash the first line in the chunk we want to compare, and only get the chunk where the first line matches in the comparison chunks. This will however have the trade-off of consuming more memory.

Another option if we only care about finding one match, instead of all matches, is to use some kind of heuristic to sort the chunks in the most likely to be a clone, and then start by looking for matches in those, and using an early return if a match is found.

# Question 3
We can see from the analysis that as the number of files grow, the variance in the time it takes for the processing increases, with the maximum time increasing linearly. We can also see that the maximum time increases about an order of magnitude faster than the average time. We also see some spikes in the data, which can probably be explained by external factors resulting from not running the application in a controlled environment.

Looking at the ratio between the total time and the time for calculating the matches, we can see that in the beginning, the overhead of preprocessing, transforming and storing the file has a not insignificant effect on the processing time, while as the number of files increases the time for perfoming the matches takes up most of the processing time. I also tried to fit a logistic regression curve for this data, which almost worked...

Looking at the moving averages for the processing times, we can see that, except for the outlier spikes in the data, the average processing time also increases linearly with the number of files processed.

Looking at the total size of the files processed, we can see that it is 179 MiB. With a chunk size of 5, we store at least 6 times that (5 times for each chunk + 1 for the original data), resulting in almost 1GB of RAM needed. With the filterLines transformation this is reduces by a bit, but it is still a lot of data that needs to be stored in memory.

One interesting attribute to look at that was not included in the data is how the processing time increases with the number of clones found.
