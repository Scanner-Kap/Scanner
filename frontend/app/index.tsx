import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  StatusBar,
  ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

export default function HomeScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.flagContainer}>
            <Text style={styles.flag}>🇮🇳</Text>
          </View>
          <Text style={styles.title}>India First</Text>
          <Text style={styles.subtitle}>FMCG Product Intelligence</Text>
        </View>

        {/* Info Box */}
        <View style={styles.infoBox}>
          <Text style={styles.infoText}>
            Scan FMCG products to instantly know if they support Indian interests.
            Make informed, patriotic choices!
          </Text>
        </View>

        {/* Main Action Buttons */}
        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[styles.actionButton, styles.primaryButton]}
            onPress={() => router.push('/scanner')}
            activeOpacity={0.8}
          >
            <Ionicons name="scan" size={32} color="#fff" />
            <Text style={styles.buttonText}>Scan Barcode</Text>
            <Text style={styles.buttonSubtext}>Quick product lookup</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, styles.secondaryButton]}
            onPress={() => router.push('/search')}
            activeOpacity={0.8}
          >
            <Ionicons name="search" size={32} color="#FF9933" />
            <Text style={[styles.buttonText, styles.secondaryButtonText]}>
              Search Brands
            </Text>
            <Text style={[styles.buttonSubtext, styles.secondaryButtonSubtext]}>
              Find product info
            </Text>
          </TouchableOpacity>
        </View>

        {/* Features */}
        <View style={styles.featuresContainer}>
          <Text style={styles.featuresTitle}>What We Check</Text>
          
          <View style={styles.featureItem}>
            <Ionicons name="business" size={20} color="#138808" />
            <Text style={styles.featureText}>Indian Company Ownership</Text>
          </View>
          
          <View style={styles.featureItem}>
            <Ionicons name="location" size={20} color="#138808" />
            <Text style={styles.featureText}>Manufacturing Location</Text>
          </View>
          
          <View style={styles.featureItem}>
            <Ionicons name="globe" size={20} color="#138808" />
            <Text style={styles.featureText}>Country Relations</Text>
          </View>
          
          <View style={styles.featureItem}>
            <Ionicons name="people" size={20} color="#138808" />
            <Text style={styles.featureText}>Indian Employment</Text>
          </View>
          
          <View style={styles.featureItem}>
            <Ionicons name="shield-checkmark" size={20} color="#138808" />
            <Text style={styles.featureText}>Data Sovereignty</Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  scrollContent: {
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 30,
  },
  flagContainer: {
    marginBottom: 16,
  },
  flag: {
    fontSize: 64,
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#FF9933',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.8,
  },
  infoBox: {
    backgroundColor: '#16213e',
    padding: 20,
    borderRadius: 12,
    marginBottom: 30,
    borderLeftWidth: 4,
    borderLeftColor: '#138808',
  },
  infoText: {
    color: '#fff',
    fontSize: 15,
    lineHeight: 22,
  },
  buttonContainer: {
    gap: 16,
    marginBottom: 30,
  },
  actionButton: {
    padding: 24,
    borderRadius: 16,
    alignItems: 'center',
    minHeight: 140,
    justifyContent: 'center',
  },
  primaryButton: {
    backgroundColor: '#FF9933',
  },
  secondaryButton: {
    backgroundColor: '#fff',
    borderWidth: 2,
    borderColor: '#FF9933',
  },
  buttonText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 12,
  },
  secondaryButtonText: {
    color: '#FF9933',
  },
  buttonSubtext: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.8,
    marginTop: 4,
  },
  secondaryButtonSubtext: {
    color: '#333',
    opacity: 0.7,
  },
  featuresContainer: {
    backgroundColor: '#16213e',
    padding: 20,
    borderRadius: 12,
  },
  featuresTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12,
  },
  featureText: {
    color: '#fff',
    fontSize: 15,
  },
});
