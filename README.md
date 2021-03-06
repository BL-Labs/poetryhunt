# Poetry Hunt
Attempting k-means clustering on text metric analysis to group together pages of newspaper text that likely have poetry on them.

## Introduction
There was a considerable amount of poetry published in newspapers during the 18th century. The exact amount is not known as it is exceedingly difficult to find it with the millions of pages that have been digitised. Working with Dr Jennifer Batt, BL Labs attempted a number of means of rating how likely a section of text is a poem. The main method attempted focussed on the placement of text in a given newspaper column, and how the indent and spacing varied compared to other text in a column. The idea was to rate this, and other signals (like % of lines in a block of text that start with a capital letter) and then use a clustering method to separate the texts with an aim to cluster all the poetry together.

## Researcher Dr Jennifer Batt
Jennifer Batt is Lecturer in English at the University of Bristol. Her research focuses on eighteenth-century poetry, with a particular interest in the ways that verse is printed and reprinted across a range of different media.  The project has three goals: first, to use data-mining techniques  to develop an index to the verse printed in newspapers in the mid-eighteenth century which will not only bring long-forgotten poems back to scholarly notice but will also shed new light on works with which literary scholars are already familiar; second, to use visualization tools to underpin a data-driven analysis of the nature and scope of newspaper-enabled poetic culture in the mid-eighteenth century; and third, to develop a workflow and a set of tools and approaches that could, in subsequent projects, be put to use to explore a much larger dataset. 

This work has been done in discussion with the IMLS funded AIDA project (http://aida.unl.edu/), which also seeks to identify poetic content in newspapers over a similar period. Adam Farquhar serves on the AIDA advisory board. AIDA is using a complementary approach to identify poetic content. Future work could contrast the two techniques and the Batt training set will be provided to the AIDA team to support their analysis.

## Notes
The following tasks in the development of the project were completed:
- OCR text from over 1 million digitised 18th Century newspaper pages were ‘scraped’ from Analyzed Layout and Text Object (ALTO) XML generated by OCR software (ABBY Finereader) and uploaded onto a secure virtual server to make a queryable text dataset for this and other future projects.
- A private Juptyer Notebook instance was generated to allow the researcher to access the text, view and write code, and query the OCR dataset.
- Ground truth of Poems and ‘Not Poems’ created by Jennifer Batt. A full year's worth of two newspapers was read and any poems discovered were marked and cited.
- Cluster data, identifying 40,000 blocks of text that are likely ‘Poems’ gathered from Burney Newspaper Corpus
- Collaboration with John O’Brien
- The newspaper clusters were augmented with links to view the relevant pages on the Gale 'Artemis' service (service in beta)
- Event organised for World Poetry day, which Dr Batt spoke at.
- A video interview with Jennifer summarising her work available through the Labs Youtube Channel (http://goo.gl/3cOSBm).

## Method
The quality of the OCR was particularly poor - it had been attempted in 2007 on images that had been crudely post-processed (to current sensibilities) to a bitonal gamut using non-adaptive thresholding with some unknown degree of colour levelling beforehand. This results in glyphs which can have lots of gaps which make reading quite difficult.

Given these issues, and the lower accuracy of the OCR, text placement and spacing seemed to be a more comparatively reliable way to analyse the text. During the time period of interest, the assumed fashion is that poems are published with much more spacing and variance in line lengths than in other blocks of typeset prose. Working on this basis, BL Labs with the help of Dr Batt worked on code to measure these relevant features in the text and to iterate through as many tests as possible in the short time frame of the project to get the best possible relavant measures. Line variance (the degree to which the placement, indenting and length of a line of text varies from the norm) was not enough to separate out the blocks of text into the desired categories. There is the beginnings of something useful but there is too much variation in the normal layout of text for this to be enough on its own. (https://github.com/BL-Labs/poetryhunt/blob/master/Cluster%20experiment%202.ipynb)

Various other signals were measured and either discarded (placement of conjunctions, pronouns and punctuation - OCR just wasn't reliable enough) or kept (% of lines that start with a capital letter, % of 'words' that start with a numeral and are likely numbers, etc). This provided better separation, but it is still not enough for an excellent and clear cluster without many false positives. However, by comparing the clustering to a gold standard (all the poems locations within two newspapers during one year), we find that the vast majority of these are located in a single cluster which provides some validation of the method (https://github.com/BL-Labs/poetryhunt/blob/master/Check%20Coverage.ipynb)
