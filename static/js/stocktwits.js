// Descending
function binaryInsert(wordToInsert, sortedFrequencyList) {
    if (sortedFrequencyList.length < 1) {
        sortedFrequencyList.push(wordToInsert);
    } else {
        // allowed to splice out of bounds, appends to the end.
        sortedFrequencyList.splice(findSpot(wordToInsert, sortedFrequencyList), 0, wordToInsert);
    }

    return sortedFrequencyList;
}


// Helper function
function findSpot(wordToInsert, sortedFrequencyList, start, end) {
    start = start || 0;
    end = end || sortedFrequencyList.length - 1;
    var pivotIndex = parseInt(start + ((end - start) / 2), 10); // rounds down by default

    var pivotWordSize = sortedFrequencyList[pivotIndex].size;
    var wordToInsertSize = wordToInsert.size;

    if (wordToInsertSize < sortedFrequencyList[end].size) return end + 1;
    if (wordToInsertSize > sortedFrequencyList[start].size) return start;

    if ((end - start <= 1) || pivotWordSize == wordToInsertSize) return pivotIndex + 1;

    if (wordToInsertSize < pivotWordSize) {
        return findSpot(wordToInsert, sortedFrequencyList, pivotIndex, end);
    } else {
        return findSpot(wordToInsert, sortedFrequencyList, start, pivotIndex);
    }
}


// Make sure everything fits on the screen
function calculateWordVolume(wordList, screenVolume) {
    screenVolume = (screenVolume * (3/4));  // long words don't fit screen volume is scaled down

    var min = 10;
    var max = 30;
    var biggest = wordList[0];
    var smallest = wordList[wordList.length - 1];

    var wordVolume = 0;
    var fontSizeTest = document.getElementById("fontSizeTest");

    // get the word that will take up the most space
    var longestWord = biggest;
    var longestWordLength = longestWord.text.length;
    for (i = 0; i < wordList.length; i++) {
        if (wordList[i].text.length > longestWordLength) {
            longestWordLength = wordList[i].text.length;
            longestWord = wordList[i];
        }
    }

    while (wordVolume < screenVolume) {
        // reset these every iteration
        wordVolume = 0;
        var scaleFontSize = d3.scale.linear()  // sqrt, linear, log, quantile, quantize.
            .domain([smallest.size, biggest.size])
            .range([min, max]);

        for (i = 0; i < wordList.length; i++) {
            var currentWord = longestWord;
            currentWord.size = wordList[i].size;
            fontSizeTest.innerHTML = currentWord.text;
            fontSizeTest.style.fontSize = (scaleFontSize(currentWord.size) + "px");
            wordVolume += (($("#fontSizeTest").width() + 10) * ($("#fontSizeTest").height() + 10));    // padding
            if (wordVolume >= screenVolume) {   // short circuit
                max = (max - 15);
                min = (max / 3);
                return { "min" : min, "max" : max };
            }
        }

        // we haven't taken up all the room in the svg yet, go bigger.
        max = (max + 15);   // don't want to increase by too small of increments or this would take forever
        min = (max / 3);    // divided by 3 looks good on the screen, no scientific reason.
    }

    return { "min" : min, "max" : max };
}


// Hyperlink everything that can be hyperlinked
function linkEverything(post) {
    // Need to do this regex first
    var linkedLinks = post.replace(/(http|https):\/\/\S+/gi,
            function linkLink(linkToPumpArticle) {
            var link = "<a class='ellipses-style' href='" + linkToPumpArticle + "'>";
            return link + linkToPumpArticle + "</a>";
        });

    var linkedCashtags = linkedLinks.replace(/\$[a-zA-Z_\.]+(?=\W|$)/g,
        function linkCashTag(cashtag) {
            var link = "<a href='https://stocktwits.com/symbol/" + cashtag.substring(1, cashtag.length) + "'>";
            return link + cashtag + "</a>";
        });

    var linkedAts = linkedCashtags.replace(/@[a-zA-z0-9_]{3,24}(?=\W|$)/g,
            function linkAt(atUser) {
            var link = "<a href='https://stocktwits.com/" + atUser.substring(1, atUser.length) + "'>";
            return link + atUser + "</a>";
        });

    return linkedAts;
}
