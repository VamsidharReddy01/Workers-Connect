package com.workersbridge.automation.utils;

import com.aventstack.extentreports.ExtentReports;
import com.aventstack.extentreports.ExtentTest;
import com.aventstack.extentreports.reporter.ExtentSparkReporter;
import com.aventstack.extentreports.reporter.configuration.Theme;

public class ExtentReporter {

    private static ExtentReports extent;
    private static final ThreadLocal<ExtentTest> testLogger = new ThreadLocal<>();

    public static ExtentReports getReporter() {
        if (extent == null) {
            String path = System.getProperty("user.dir") + "/reports/latest/execution-report.html";
            ExtentSparkReporter reporter = new ExtentSparkReporter(path);
            reporter.config().setReportName("Android Appium E2E Automation Results");
            reporter.config().setDocumentTitle("Test Results");
            reporter.config().setTheme(Theme.STANDARD);

            extent = new ExtentReports();
            extent.attachReporter(reporter);
            extent.setSystemInfo("QA Engineer", "Automation");
            extent.setSystemInfo("Platform", "Android");
        }
        return extent;
    }

    public static ExtentTest startTest(String testName) {
        ExtentTest test = getReporter().createTest(testName);
        testLogger.set(test);
        return test;
    }

    public static ExtentTest getTest() {
        return testLogger.get();
    }
    
    public static void flush() {
        if (extent != null) {
            extent.flush();
        }
    }
}
