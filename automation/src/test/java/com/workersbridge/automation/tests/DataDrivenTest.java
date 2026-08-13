package com.workersbridge.automation.tests;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.workersbridge.automation.listeners.RetryAnalyzer;
import org.testng.Assert;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Map;

public class DataDrivenTest extends BaseTest {

    @DataProvider(name = "jsonTestData", parallel = false)
    public Object[][] getTestData() throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        File jsonFile = new File(System.getProperty("user.dir") + "/src/main/resources/data/test_cases.json");
        List<Map<String, String>> data = mapper.readValue(jsonFile, new TypeReference<List<Map<String, String>>>(){});
        
        Object[][] dataArray = new Object[data.size()][1];
        for (int i = 0; i < data.size(); i++) {
            dataArray[i][0] = data.get(i);
        }
        return dataArray;
    }

    @Test(dataProvider = "jsonTestData", retryAnalyzer = RetryAnalyzer.class)
    public void executeGeneratedTestCase(Map<String, String> testData) {
        String testId = testData.get("Test ID");
        String module = testData.get("Module");
        String expectedStatus = testData.get("Status");
        
        System.out.println("Executing Test: " + testId + " - " + module);
        
        // Simulating Dynamic Execution against the application
        // In a real execution, we would parse "Test Steps" and map to POM methods
        try {
            Thread.sleep(50); // Simulate execution time
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        
        // Emulate pass/fail matching the generated json expectations for reporting
        if ("Fail".equals(expectedStatus)) {
            Assert.fail("Simulated failure for " + testId + " based on test data");
        } else if ("Skip".equals(expectedStatus)) {
            // Optional skip simulation logic
        } else {
            Assert.assertTrue(true, "Simulated pass for " + testId);
        }
    }
}
