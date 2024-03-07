"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var openweather_library_1 = require("../utils/openweather_library");
var main_1 = require("../src/main");
// Test end to end
// There will be a couple of logging errors, as the tests will complete before logging finishes. 
describe("Full pipeline test", function () {
    it("Pipeline should run, not return a  value", function () {
        //baseline endpoint
        var endpoint = "weather?";
        // Create URL
        var webUrl = (0, openweather_library_1.createOpenWeatherUrl)(endpoint);
        // Get weather data
        (0, main_1.getWeatherData)(webUrl)
            .then(function (result) {
            // parse data - finish extraction
            var payload = (0, main_1.parseData)(result);
            expect((0, main_1.writeData)(payload)).toBeUndefined();
        });
    });
});
// Bad endpoint/API call - validating that it's caught and error message sent
describe("API Call - Exception Handling Test", function () {
    it("API Call Should Fail and return error message", function () {
        // Create URL
        var webUrl = (0, openweather_library_1.createOpenWeatherUrl)("?cheese");
        // define message 
        var message = { "message": "Request failed with status code 401", "status": 401 };
        // Get weather data
        (0, main_1.getWeatherData)(webUrl)
            .then(function (result) {
            expect(result).toContain(message);
        });
    });
});
// Validate sending bad data for validation 
describe("Validate data format", function () {
    it("Data format validation should fail", function () {
        var bad_data = {
            "c": 378.85,
            "d": 2.7,
            "dp": -1.006,
            "h": 384.3,
            "l": 377.44,
            "o": 383.76,
            "pc": 382.7,
            "t": 170129160
        };
        //validate data
        expect((0, openweather_library_1.validateJson)(bad_data)).toEqual(1);
    });
});
// Validate sending Slack Alert
// This is just to generate a message, i.e., this test always passes
// the tester will need to check their Slack messages to verify the message
// went through.
describe("Validate data format", function () {
    it("Data format validation should fail", function () {
        var message = "Test Slack Alert";
        //validate data
        expect((0, openweather_library_1.sendSlackAlerts)(message)).toBeUndefined();
    });
});
