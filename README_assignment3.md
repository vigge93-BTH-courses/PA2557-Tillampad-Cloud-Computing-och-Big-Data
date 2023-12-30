# Question 1
With the original cljdetector program, I was unable to process the entire corpus, due to a bug in the program. When iterating over the files in the corpus, it would match any file with the pattern `*.java`. The problem arose with some of the code-bases having directories named with the same pattern e.g. `jellytools.java` in the `netbeans` repository. This caused the file processing to silently fail when trying to read a directory as a file, resulting in only 2100 files read. After fixing that bug, I was able to process the entire data set in ~6.5 hours.

# Question 2
## Collected data
![Logs](assets/logs.png)
![Alt text](assets/files.png)
![Alt text](assets/chunks.png)
![Alt text](assets/candidates.png)
![Alt text](assets/clones.png)

## Time to generate chunks
The number of chunks generated increases linearly with time, which indicates that the time to generate each chunk is constant. This makes sense, since the processing of chunks for one file is not dependent on the processing of chunks for the other files.

## Time to generate candidates
I cannot answer this question empirically, since all of the processing to generate candidates were done in the database, and it did not give continuous output of the results. However, reasoning about the process, we would expect theoretical time to be constant for each candidate, since we use the hash to find all the similar chunks. However, since MongoDB is not a hashtable, and since we don't have any index for the chunkHash, finding all matching chunks requires a linear search through the entire collection, resulting in the processing time for each chunk increasing linearly with the number of chunks in the database. Also, depending on how MongoDB handles the aggregate function, the time may or may not be dependent on the number of already processed candidates, depending on if MongoDB consideres already matched candidates as "consumed".

## Time to expand clone candidates
As we can see in the graph, the number of candidates decreases linearly with time, indicating that the time to process each candidate is constant. However, we can also see that the number of clones increases superlinearly, indicating that the time to find new clones decreases as the number of candidates decreases, alternatively the number of clones found for each candidate increases the more candidates are processed.

## Average clone size
```db.clones.aggregate([{$addFields: {"instance": {$first: "$instances"}}}, {$project: { length: {$subtract: ["$instance.endLine", "$instance.startLine"]}}}, {$group: {_id: 0, average: {$avg: "$length"}}}])```

The average clone size is 52.2 lines long. Since every candidate is either part of an existing clone, or considered a new clone, and we know the number of lines per chunk, we can use this to calculate progress by comparing number of lines in the found clones compared to the total number of lines in the candidates compared to the average clone size. With this we should be able to get an estimate of the total number of clones that exist. The exact calculations required are left as an implementation detail.

## Average chunks per file
```db.chunks.aggregate([{$addFields: {fileName: "$fileName"}}, {$group: {_id: "$fileName", count: { $count: {}}}}, {$group: {_id: 0, average: {$avg: "$count"}}}])```

The average number of chunks per file is 159.9 chunks. During the read phase, this does not help us very much. During the chunkify phase, we can predict progress by looking at the number of chunks added to the collection, and then dividing by average number of chunks per file to give us an estimate of how many of the files that have been processed. For the identify candidates stage, we have the same problem as above, that the aggregate command is essentially a black box that gives little insight into the progress of the command.