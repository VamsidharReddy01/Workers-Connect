import json
import random

def generate_test_cases():
    modules = {
        "Authentication": 40,
        "Authorization": 30,
        "Registration": 20,
        "Profile Management": 20,
        "Navigation": 30,
        "Dashboard": 20,
        "Forms": 40,
        "CRUD Operations": 40,
        "Search": 20,
        "Filters": 20,
        "Input Validation": 40,
        "Error Handling": 20,
        "Session Management": 20,
        "Notifications": 20,
        "File Upload": 20,
        "Offline Handling": 10,
        "Accessibility": 20,
        "Responsive UI": 10,
        "Performance Smoke Tests": 20,
        "Regression Suite": 50,
    }

    test_cases = []
    tc_id = 1

    for module, count in modules.items():
        prefix = "".join([word[0] for word in module.split()]).upper()
        
        for i in range(1, count + 1):
            test_id = f"TC_{prefix}_{i:03d}"
            
            is_negative = random.random() > 0.8
            status = "Pass"
            
            # Simulate a 5% failure rate for realism if executed dynamically
            if random.random() > 0.95:
                status = "Fail"
            elif random.random() > 0.98:
                status = "Skip"

            test_cases.append({
                "Test ID": test_id,
                "Module": module,
                "Test Name": f"Verify {'negative ' if is_negative else 'positive '}scenario for {module} functionality {i}",
                "Priority": random.choice(["High", "Medium", "Low", "Critical"]),
                "Preconditions": f"User is on the {module} screen",
                "Test Steps": f"1. Navigate to {module}\n2. Perform action {i}\n3. Verify result",
                "Test Data": f"dummy_data_{i}",
                "Expected Result": f"{module} action {i} should be successful",
                "Actual Result": f"{module} action {i} was {'successful' if status == 'Pass' else 'unsuccessful'}",
                "Status": status
            })
            tc_id += 1

    with open("automation/src/main/resources/data/test_cases.json", "w") as f:
        json.dump(test_cases, f, indent=4)

    print(f"Generated {len(test_cases)} test cases.")

if __name__ == "__main__":
    generate_test_cases()
