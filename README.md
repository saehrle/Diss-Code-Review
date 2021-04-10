# Diss-Code-Review
Für GV zum Code reviewen.

Das ist jetzt erstmal `Teil 1: Das Finden der Content Words`.

Daraus entsteht später eine Lookup-Table, die fast fertig ist. Die Loopup-Table beinhaltet ein Commandline-Tool, das einen beim Schreiben des RDF unterstützt (also vorgefertigte Lösungen für die häufigsten Möglichkeiten anbietet).
Weiterhin ein Dings zum Annotieren und zum KWICs erstellen.

Dann noch eines um daraus gewisses RDF bereits vorzuberechnen.

# Teil 1: Das Finden der Content Words
1. Alle möglichen Texte werden als Corpus eingelesen und tokenisiert (CLTK_Latin). Es wird auch ein Bag of Words daraus erstellt, allerdings nicht (!) lemmatisiert. Dies hat den Grund, dass gewisse Quelldaten der HAB alle möglichen Sonderzeichen in der Transkription erhalten haben - und wenn man die nicht jetzt einfach wegwerfen will, müssen all diese Sonderformen verzeichnet werden (dazu später). 
2. Eine Basic-Stopword-Liste wird erstellt, sofern es noch keine gibt - ansonsten wird die bereits als `stop_word_list.txt` vorliegende eingelesen.
3. Zudem gibt es ein `content_words.txt` - wie im Fall des Stop-Word-Txt wird dieses erstellt, sofern nicht vorhanden oder eingelesen, sofern vorhanden. Dieses wird in ein `dict` übersetzt, dass einen sozusagen 'lemmatisierten' Word Count erstellt und dabei alle unterschiedlichen Lemmata einberechnet. Auch speichert er alle Formen, wie ein Wort aufgetreten ist. Diese Liste wird später für die Annotation verwendet, wodurch auch alle möglichen Sonderschreibweisen annotiert werden können. Allerdings kann es sein, dass bei der Lemmatisierung Fehler auftreten (CLTK ist da recht durchwachsen). Hierin liegt der zweite Vorteil, eine Datei zwischenzuspeichern - denn dort kann ich die Fehl-Lemmata wieder rauslöschen. 
4. Aus dieser Liste wird in der Folge eine Lookup-Table erstellt, die zwischen SKOS-Labels, Concepts usw. vermittelt und aus der dann SKOS und RDF generiert werden. 

Die Word-Counts sind an sich egal und ich habe auch nicht verifiziert, ob das komplizierte System, diese beim Fund neuer Schreibungen upzudaten 100% funktioniert. Allerdings nutze ich den Word-Count nur ungefähr dafür, ggf. zu priorisieren, indem ich nur die häufigsten Wörter tiefenerschließe. Dafür sollte auch ein nicht-perfekter Word-Count genügen.

Das Programm braucht, wenn man das ganze in `corpus` abgelegte (und nicht wirklich OCR-korrigierte) Korpus reinliest, relativ lang zum Rechnen. Nachdem die Processing-Reihenfolge allerdings nach Häufigkeit geordnet ist, wird das relativ schnell weniger.
