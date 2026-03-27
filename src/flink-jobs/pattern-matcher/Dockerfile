# --- Build stage ---
FROM maven:3.9-eclipse-temurin-11 AS builder

WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src/ src/
RUN mvn package -DskipTests -B

# --- Runtime stage ---
FROM flink:1.20

COPY --from=builder /build/target/pattern-matcher-0.1.0.jar /opt/flink/usrlib/pattern-matcher.jar
