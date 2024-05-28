.PHONY: build

build:
	cd ballet-planner-mus && mvn package
	mv ballet-planner-mus/target/ballet-planner-mus-1.0-SNAPSHOT.jar ./ballet-planner-mus-1.0-SNAPSHOT.jar
