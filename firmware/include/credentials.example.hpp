#pragma once

// Copy to credentials.hpp and replace the placeholders locally.
// Never commit the resulting credentials.hpp file.

constexpr char kWifiSsid[] = "replace-me";
constexpr char kWifiPassword[] = "replace-me";
constexpr char kAwsIotEndpoint[] = "replace-me-ats.iot.us-east-1.amazonaws.com";
constexpr char kDeviceId[] = "charger-001";

constexpr char kRootCa[] = R"PEM(
-----BEGIN CERTIFICATE-----
replace-me
-----END CERTIFICATE-----
)PEM";

constexpr char kDeviceCertificate[] = R"PEM(
-----BEGIN CERTIFICATE-----
replace-me
-----END CERTIFICATE-----
)PEM";

constexpr char kPrivateKey[] = R"PEM(
-----BEGIN PRIVATE KEY-----
replace-me
-----END PRIVATE KEY-----
)PEM";
