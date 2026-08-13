package com.workersbridge.automation.pages;

import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;

public class AuthPage extends BasePage {

    @FindBy(xpath = "//android.widget.EditText[@content-desc='Email address']")
    private WebElement emailInput;

    @FindBy(xpath = "//android.widget.EditText[@content-desc='Password']")
    private WebElement passwordInput;

    @FindBy(xpath = "//android.widget.Button[@content-desc='Login']")
    private WebElement loginButton;

    @FindBy(xpath = "//android.widget.TextView[@content-desc='Error Message']")
    private WebElement errorMessage;

    public AuthPage enterEmail(String email) {
        type(emailInput, email);
        return this;
    }

    public AuthPage enterPassword(String password) {
        type(passwordInput, password);
        return this;
    }

    public void clickLogin() {
        click(loginButton);
    }

    public boolean isErrorMessageDisplayed() {
        return isElementDisplayed(errorMessage);
    }

    public String getErrorMessageText() {
        return getText(errorMessage);
    }
}
