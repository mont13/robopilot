import { Stack } from "expo-router";
import { useFrameworkReady } from "../hooks/useFrameworkReady";
import { View, Text, StyleSheet } from "react-native";
import { StatusBar } from "expo-status-bar";

export default function RootLayout() {
  const isReady = useFrameworkReady();

  if (!isReady) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading RoboPilot...</Text>
      </View>
    );
  }

  return (
    <>
      <StatusBar style="dark" />
      <Stack>
        <Stack.Screen
          name="index"
          options={{
            headerShown: false,
            title: "RoboPilot",
          }}
        />
        <Stack.Screen
          name="+not-found"
          options={{
            title: "Not Found",
            presentation: "modal",
          }}
        />
      </Stack>
    </>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "white",
  },
  loadingText: {
    fontSize: 18,
    color: "#6B7280",
    fontWeight: "500",
  },
});
