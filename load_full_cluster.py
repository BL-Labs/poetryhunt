from clustering_capitals import create_cluster_dataset, NewspaperArchive
DBFILE = "full.db"
n = NewspaperArchive(textareas="/datastore/burneytextareas")
ds = create_cluster_dataset(n, daterange = [1700, 1800], dbfile = DBFILE)
