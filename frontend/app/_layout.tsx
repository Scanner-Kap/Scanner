import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';

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
