import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from './contexts/AuthContext';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="index" />
          <Stack.Screen name="scanner" />
          <Stack.Screen name="search" />
          <Stack.Screen name="product-detail" />
          <Stack.Screen name="brand-detail" />
          <Stack.Screen name="login" />
          <Stack.Screen name="profile" />
        </Stack>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
