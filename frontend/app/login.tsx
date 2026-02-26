import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from './contexts/AuthContext';

export default function LoginScreen() {
  const router = useRouter();
  const { signInWithGitHub, isLoading } = useAuth();
  const [signing, setSigning] = React.useState(false);

  const handleGitHubSignIn = async () => {
    setSigning(true);
    try {
      await signInWithGitHub();
      router.replace('/profile');
    } finally {
      setSigning(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Sign In</Text>
        <View style={{ width: 40 }} />
      </View>

      <View style={styles.content}>
        <View style={styles.logoContainer}>
          <Text style={styles.flag}>🇮🇳</Text>
          <Text style={styles.appName}>India First</Text>
          <Text style={styles.tagline}>Connect your GitHub account to save your preferences and scan history.</Text>
        </View>

        <View style={styles.benefitsContainer}>
          <View style={styles.benefitItem}>
            <Ionicons name="bookmark-outline" size={20} color="#FF9933" />
            <Text style={styles.benefitText}>Save favorite brands</Text>
          </View>
          <View style={styles.benefitItem}>
            <Ionicons name="time-outline" size={20} color="#FF9933" />
            <Text style={styles.benefitText}>View scan history</Text>
          </View>
          <View style={styles.benefitItem}>
            <Ionicons name="person-outline" size={20} color="#FF9933" />
            <Text style={styles.benefitText}>Personalized recommendations</Text>
          </View>
        </View>

        <TouchableOpacity
          style={[styles.githubButton, (signing || isLoading) && styles.githubButtonDisabled]}
          onPress={handleGitHubSignIn}
          disabled={signing || isLoading}
          activeOpacity={0.8}
        >
          {signing ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Ionicons name="logo-github" size={24} color="#fff" />
          )}
          <Text style={styles.githubButtonText}>
            {signing ? 'Connecting...' : 'Continue with GitHub'}
          </Text>
        </TouchableOpacity>

        <Text style={styles.disclaimer}>
          By signing in, you agree to share your public GitHub profile information with India First.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#16213e',
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  flag: {
    fontSize: 56,
    marginBottom: 12,
  },
  appName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FF9933',
    marginBottom: 12,
  },
  tagline: {
    fontSize: 15,
    color: '#aaa',
    textAlign: 'center',
    lineHeight: 22,
  },
  benefitsContainer: {
    backgroundColor: '#16213e',
    borderRadius: 12,
    padding: 20,
    marginBottom: 32,
    gap: 16,
  },
  benefitItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  benefitText: {
    color: '#fff',
    fontSize: 15,
  },
  githubButton: {
    backgroundColor: '#24292e',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    gap: 12,
    marginBottom: 16,
  },
  githubButtonDisabled: {
    opacity: 0.6,
  },
  githubButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '600',
  },
  disclaimer: {
    color: '#666',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
});
