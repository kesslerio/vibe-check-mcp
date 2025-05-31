// Test file with potential style issues for Claude lint to catch

function loadUsers() {
    // Using enum instead of union types
    enum UserType {
        ADMIN = "admin",
        USER = "user"
    }
    
    // Using three dots instead of Unicode ellipsis
    console.log("Loading users...");
    
    // Some other potential issues
    var userName = "test";  // should use const/let
    
    return {
        type: UserType.ADMIN,
        message: "Users loaded successfully..."
    };
}

// Add another function to trigger workflow update
function processData() {
    var data = getData();  // should use const/let
    console.log("Processing data...");  // should use ellipsis
    return data;
}