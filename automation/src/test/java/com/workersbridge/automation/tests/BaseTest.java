package com.workersbridge.automation.tests;

import com.workersbridge.automation.drivers.AppiumServerManager;
import com.workersbridge.automation.drivers.DriverFactory;
import com.workersbridge.automation.utils.ExcelReporter;
import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.ITestResult;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;

public class BaseTest {

    protected static List<Map<String, String>> testResults = new ArrayList<>();
    private ThreadLocal<Long> startTime = new ThreadLocal<>();

    @BeforeSuite
    public void globalSetup() {
        AppiumServerManager.startServer();
    }

    @BeforeMethod
    public void methodSetup() {
        DriverFactory.initDriver();
        startTime.set(System.currentTimeMillis());
    }

    @AfterMethod
    public void methodTeardown(ITestResult result) {
        long duration = System.currentTimeMillis() - startTime.get();
        
        // Log result for Excel Reporter
        Map<String, String> resultMap = new HashMap<>();
        Object[] params = result.getParameters();
        if (params.length > 0 && params[0] instanceof Map) {
            Map<String, String> testData = (Map<String, String>) params[0];
            resultMap.put("Test ID", testData.get("Test ID"));
            resultMap.put("Module", testData.get("Module"));
            resultMap.put("Test Name", testData.get("Test Name"));
            resultMap.put("Priority", testData.get("Priority"));
        } else {
            resultMap.put("Test ID", "UNKNOWN");
            resultMap.put("Test Name", result.getMethod().getMethodName());
        }
        
        String status = "SKIP";
        if (result.getStatus() == ITestResult.SUCCESS) status = "PASS";
        else if (result.getStatus() == ITestResult.FAILURE) status = "FAIL";
        
        resultMap.put("Status", status);
        resultMap.put("Execution Time", duration + "ms");
        
        synchronized (testResults) {
            testResults.add(resultMap);
        }

        DriverFactory.quitDriver();
    }

    @AfterSuite
    public void globalTeardown() {
        AppiumServerManager.stopServer();
        String reportPath = System.getProperty("user.dir") + "/reports/Automation_Test_Report.xlsx";
        ExcelReporter.generateReport(testResults, reportPath);
    }
}
