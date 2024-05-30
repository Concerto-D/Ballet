.PHONY: build

JAR_FILE=ballet-planner-mus-1.0-SNAPSHOT-shaded.jar

build:
	if [ -f $(JAR_FILE) ]; then rm $(JAR_FILE); fi
	cd ballet-planner-mus && if [ -f $(JAR_FILE) ]; then rm $(JAR_FILE); fi && mvn clean && mvn package
	mv ballet-planner-mus/target/$(JAR_FILE) ./$(JAR_FILE)
