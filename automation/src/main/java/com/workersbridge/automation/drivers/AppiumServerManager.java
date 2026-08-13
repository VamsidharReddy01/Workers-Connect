package com.workersbridge.automation.drivers;

import io.appium.java_client.service.local.AppiumDriverLocalService;
import io.appium.java_client.service.local.AppiumServiceBuilder;

import java.io.File;

public class AppiumServerManager {
    
    private static AppiumDriverLocalService service;

    public static void startServer() {
        if (service == null || !service.isRunning()) {
            AppiumServiceBuilder builder = new AppiumServiceBuilder()
                    .withIPAddress("127.0.0.1")
                    .usingPort(4723)
                    // You can specify the JS path to appium if not in system PATH
                    // .withAppiumJS(new File("/path/to/appium/main.js"))
                    .withArgument(() -> "--log-level", "error"); // Reduce log verbosity

            service = AppiumDriverLocalService.buildService(builder);
            service.start();
            System.out.println("Appium server started at: " + service.getUrl());
        }
    }

    public static void stopServer() {
        if (service != null && service.isRunning()) {
            service.stop();
            System.out.println("Appium server stopped.");
        }
    }
}
