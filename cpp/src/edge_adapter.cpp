#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>

namespace {

std::string trim(const std::string& text) {
    const char* whitespace = " \t\r\n";
    const auto first = text.find_first_not_of(whitespace);
    if (first == std::string::npos) {
        return "";
    }
    const auto last = text.find_last_not_of(whitespace);
    return text.substr(first, last - first + 1);
}

// Empty, non-numeric and non-finite values are forwarded as "NA".
std::string normalize_value(const std::string& raw) {
    const std::string text = trim(raw);
    if (text.empty()) {
        return "NA";
    }
    char* end = nullptr;
    const double parsed = std::strtod(text.c_str(), &end);
    if (*end != '\0' || !std::isfinite(parsed)) {
        return "NA";
    }
    return text;
}

}  // namespace

int main() {
    std::cout << "timestamp,value\n";

    std::string line;
    while (std::getline(std::cin, line)) {
        line = trim(line);
        if (line.empty() || line == "timestamp,value") {
            continue;
        }

        const auto separator = line.find(',');
        const std::string timestamp =
            separator == std::string::npos ? "" : trim(line.substr(0, separator));
        if (timestamp.empty()) {
            std::cerr << "Registro ignorado: formato invalido\n";
            continue;
        }

        std::cout << timestamp << ',' << normalize_value(line.substr(separator + 1)) << '\n';
    }
}
