Dieses Tool stellt einen Prototyp zur automatisierten Identifikation von Fehlerursachen in Microservices dar. Dazu wird Tracing (Jaeger und OpenTracing) verwendet.

Für die Nutzung des Prototyps ist nachfolgend eine kurze Anleitung beschrieben. Für die Testdurchführung ist hierbei die exemplarische Anwendung \glqq Automatic Umbrella\grqq{} verwendet worden. Das Konzept kann jedoch auf jede Microservice-basierte Anwendung in Python übertragen werden. Voraussetzung hierfür ist die vollständige Implementierung von Tracing mit Jaeger.

## Start der exemplarischen Anwendung 

Die Anwendung kann über das Repository von Github geklont und über Docker Compose gestartet werden. Dazu müssen Git, Docker und Docker Compose installiert sein. Folgendes Listing beschreibt das Klonen sowie Starten der Anwendung.

```
$ git clone https://github.com/rsinner99/automatic-umbrella.git
$ cd automatic-umbrella
$ docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Folgende Container der Anwendung sind nun über http://localhost:{port} erreichbar. Der Port ist dabei je nach Service zu wählen. Die Angabe von Port 80 ist optional.

* Frontend (Nginx): http://localhost:80/frontend
* API (Nginx): http://localhost:80/API
* Flower (Celery Task Monitoring): http://localhost:80/flower
* Elasticsearch (Tracing): http://localhost:9200
* Kibana (Tracing): http://localhost:5601
* Jaeger UI (Tracing): http://localhost:16686


### Initialisierung der Anwendung mit Testdaten

Um die Anwendung nutzen zu können, müssen einige Testdaten in der Datenbank vorhanden sein. Besonders wichtig ist ein Nutzerkonto zur Anmeldung. Folgender Befehl importiert bereits vorhandene Testdaten. 

```
$ docker exec -i umbrella_db sh -c 'exec mysql -uroot -proot' < ./e2e_tests/testdata.sql
```

Für den Login stehen folgende Anmeldedaten zur Verfügung: Nutzername "test" und Passwort "test1234test" (ohne Anführungszeichen).


## Erstellen eines Containers zur Testausführung

Um die Ende-zu-Ende Tests der Anwendung ausführen zu können, kann ein zusätzlicher Container verwendet werden, um die Ausführung vom Host zu isolieren. Dazu wird existiert ein Dockerfile im Repository der exemplarischen Anwendung. Es werden alle benötigten Python Module und auch der Prototyp zur Trace-Analyse installiert. Die Variable "docker\_host" sollte durch die IP-Adresse des Docker-Hosts ersetzen werden. Unter dieser IP-Adresse sollte der Host für den Container erreichbar sein.

```
$ cd e2e_tests
$ docker build -f Dockerfile -t umbrella_test_runner --build-arg docker_host=172.17.0.1 .
```

### Ausführung der Tests

Zur Testausführung wird der Container gestartet und ein lokales Verzeichnis des Hosts hinein gemounted. Dadurch können die Auswertungsberichte später auf dem Host eingesehen werden. Anschließend werden die Tests mithilfe des Unittest-Frameworks von Python durchführt. Zuletzt wird die Auswertung der Tests mithilfe des Prototyps über den Befehl "TraceExplorer" gestartet.

```
$ mkdir reports # Verzeichnis für die Auswertungsberichte in HTML: Auf dem Host verfuegbar
$ docker run -d -v $(pwd)/reports:/code/eval_reports --add-host=host.docker:172.17.0.1 --name e2e_runner umbrella_test_runner
$ docker exec -it e2e_runner python -m unittest discover # Testausfuehrung
$ docker exec -it e2e_runner TraceExplorer # Trace-Auswertung
```
