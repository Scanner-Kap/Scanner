import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Alert } from 'react-native';

// Catch and display JS errors on device for debugging
if (typeof ErrorUtils !== 'undefined') {
  const originalHandler = ErrorUtils.getGlobalHandler();
  ErrorUtils.setGlobalHandler((error, isFatal) => {
    Alert.alert(
      isFatal ? 'Fatal Error' : 'JS Error',
      error?.message + '\n\n' + (error?.stack?.slice(0, 500) ?? ''),
    );
    originalHandler(error, isFatal);
  });
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="scanner" />
        <Stack.Screen name="search" />
        <Stack.Screen name="product-detail" />
        <Stack.Screen name="brand-detail" />
      </Stack>
    </SafeAreaProvider>
  );
}
