package com.workersbridge.automation.listeners;

import com.aventstack.extentreports.ExtentTest;
import com.aventstack.extentreports.Status;
import com.workersbridge.automation.utils.ExtentReporter;
import com.workersbridge.automation.utils.ScreenshotUtils;
import org.testng.ITestContext;
import org.testng.ITestListener;
import org.testng.ITestResult;

public class TestListener implements ITestListener {

    @Override
    public void onStart(ITestContext context) {
        System.out.println("Test Suite Started: " + context.getName());
    }

    @Override
    public void onFinish(ITestContext context) {
        ExtentReporter.flush();
        System.out.println("Test Suite Finished");
    }

    @Override
    public void onTestStart(ITestResult result) {
        ExtentReporter.startTest(result.getMethod().getMethodName());
    }

    @Override
    public void onTestSuccess(ITestResult result) {
        ExtentTest test = ExtentReporter.getTest();
        if (test != null) {
            test.log(Status.PASS, "Test Passed");
        }
    }

    @Override
    public void onTestFailure(ITestResult result) {
        ExtentTest test = ExtentReporter.getTest();
        if (test != null) {
            test.log(Status.FAIL, "Test Failed: " + result.getThrowable());
            try {
                String screenshotPath = ScreenshotUtils.captureScreenshot(result.getMethod().getMethodName());
                test.addScreenCaptureFromPath(screenshotPath);
            } catch (Exception e) {
                test.log(Status.FAIL, "Failed to attach screenshot: " + e.getMessage());
            }
        }
    }

    @Override
    public void onTestSkipped(ITestResult result) {
        ExtentTest test = ExtentReporter.getTest();
        if (test != null) {
            test.log(Status.SKIP, "Test Skipped: " + result.getThrowable());
        }
    }
}
