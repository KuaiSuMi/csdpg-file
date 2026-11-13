package dev.reynard.junit.integration.micro;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import dev.reynard.junit.FiTest;
import dev.reynard.junit.instrumentation.FaultController;
import dev.reynard.junit.instrumentation.testcontainers.InstrumentedApp;
import dev.reynard.junit.instrumentation.testcontainers.services.InstrumentedService;
import dev.reynard.junit.integration.micro.setup.MicroBenchmarkContainer;
import dev.reynard.junit.strategy.TrackedFaultload;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

/** Optional recommendation dependency: failure must preserve a valid empty list. */
public class MaturityContractIT {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final boolean REPAIRED = Boolean.parseBoolean(System.getenv("MATURITY_REPAIR"));
    private static final InstrumentedApp app = new InstrumentedApp();
    private static final InstrumentedService recommendations = app.instrument("recommendations", 8080,
            MicroBenchmarkContainer.Leaf().withEnv("RESPONSE", "[\"product-1\"]"));
    private static final InstrumentedService frontend = app.instrument("frontend", 8080,
            MicroBenchmarkContainer.PassThrough(MicroBenchmarkContainer.call(recommendations.getHostname()),
                    REPAIRED ? "[]" : "")).withExposedPorts(8080);
    private static final OkHttpClient client = new OkHttpClient.Builder()
            .connectTimeout(5, TimeUnit.SECONDS).readTimeout(10, TimeUnit.SECONDS).build();

    public static FaultController getController() { return app; }

    @BeforeAll
    static void start() {
        recommendations.start();
        frontend.start();
        app.start();
    }

    @AfterAll
    static void stop() {
        app.stop();
        frontend.stop();
        recommendations.stop();
        app.network.close();
    }

    @FiTest(failStop = false)
    void optionalRecommendation(TrackedFaultload faultload) throws Exception {
        Request request = faultload.newRequestBuilder()
                .url("http://localhost:" + frontend.getMappedPort(8080) + "/").build();
        try (Response response = client.newCall(request).execute()) {
            String body = response.body().string();
            var trace = app.getTrace(faultload);
            boolean applied = trace.getInjectedFaults().equals(faultload.getFaultload().faultSet());
            boolean passed = response.code() == 200
                    && body.equals(faultload.size() == 0 ? "[\"product-1\"]" : "[]");
            var record = JSON.createObjectNode();
            record.put("scenario", "optional-recommendation");
            record.put("phase", REPAIRED ? "after" : "before");
            record.put("service", "frontend");
            record.put("dependency", "recommendations");
            record.put("trace_id", faultload.getTraceId());
            record.put("http_status", response.code());
            record.put("body", body);
            record.put("passed", passed);
            record.put("injection_verified", applied);
            record.put("fault_count", faultload.size());
            record.set("faultload", JSON.readTree(faultload.serializeJson()));
            Request traceRequest = new Request.Builder()
                    .url(app.controllerInspectUrl + "/v1/trace/" + faultload.getTraceId()).build();
            try (Response rawTrace = client.newCall(traceRequest).execute()) {
                assertTrue(rawTrace.isSuccessful(), "controller trace retrieval failed");
                record.set("trace", JSON.readTree(rawTrace.body().string()));
            }
            Path output = Path.of(System.getenv("MATURITY_OBSERVATIONS"));
            Files.createDirectories(output);
            JSON.writerWithDefaultPrettyPrinter().writeValue(
                    output.resolve(faultload.getTraceId() + ".json").toFile(), record);
            assertTrue(applied, "requested faults must actually be injected");
            assertEquals(200, response.code(), "optional dependency must not take down the frontend");
            assertEquals(faultload.size() == 0 ? "[\"product-1\"]" : "[]", body);
        }
    }
}
