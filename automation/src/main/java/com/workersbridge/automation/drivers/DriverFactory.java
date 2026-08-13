package com.workersbridge.automation.drivers;

import io.appium.java_client.android.AndroidDriver;
import io.appium.java_client.android.options.UiAutomator2Options;
import org.openqa.selenium.Platform;
import org.openqa.selenium.WebDriverException;

import java.net.MalformedURLException;
import java.net.URL;
import java.time.Duration;

public class DriverFactory {

    private static final ThreadLocal<AndroidDriver> driver = new ThreadLocal<>();

    public static AndroidDriver getDriver() {
        return driver.get();
    }

    public static void initDriver() {
        if (getDriver() == null) {
            try {
                UiAutomator2Options options = new UiAutomator2Options()
                        .setPlatformName(Platform.ANDROID.name())
                        .setDeviceName("emulator-5554")
                        .setAutomationName("UiAutomator2")
                        .setAppPackage("com.workersbridge.app")
                        .setAppActivity("com.workersbridge.app.MainActivity")
                        .setAutoGrantPermissions(true)
                        .setNoReset(false);

                // Assuming Appium runs on localhost:4723
                URL appiumServerUrl = new URL("http://127.0.0.1:4723");

                AndroidDriver androidDriver = new AndroidDriver(appiumServerUrl, options);
                androidDriver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
                
                driver.set(androidDriver);
            } catch (MalformedURLException e) {
                throw new WebDriverException("Appium server URL is invalid", e);
            }
        }
    }

    public static void quitDriver() {
        if (getDriver() != null) {
            getDriver().quit();
            driver.remove();
        }
    }
}
