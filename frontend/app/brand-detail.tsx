import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

type Brand = {
  id: number;
  brand_name: string;
  parent_company: string;
  ownership_country: string;
  is_indian_company: boolean;
  manufactures_in_india: string;
  manufacturing_states: string[];
  employees_in_india_estimate: string;
  data_storage_country: string;
  security_flags: string[];
  govt_restrictions: string[];
  source_links: string[];
};

type ScoreData = {
  score: number;
  breakdown: any;
  recommendation: string;
};

export default function BrandDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const [brand, setBrand] = useState<Brand | null>(null);
  const [scoreData, setScoreData] = useState<ScoreData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.brandId) {
      fetchBrandData(params.brandId as string);
    }
  }, [params]);

  const fetchBrandData = async (brandId: string) => {
    try {
      const [brandResponse, scoreResponse] = await Promise.all([
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/brand/${brandId}`),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/score/${brandId}`),
      ]);
      setBrand(brandResponse.data);
      setScoreData(scoreResponse.data);
    } catch (error) {
      console.error('Error fetching brand data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return '#138808';
    if (score >= 6) return '#4CAF50';
    if (score >= 4) return '#FFC107';
    return '#F44336';
  };

  if (loading || !brand || !scoreData) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#FF9933" style={{ marginTop: 100 }} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Brand Intelligence</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView style={styles.content}>
        {/* Brand Header */}
        <View style={styles.section}>
          <View style={styles.brandHeader}>
            <View style={styles.brandIcon}>
              <Ionicons name="business" size={32} color="#FF9933" />
            </View>
            <Text style={styles.brandName}>{brand.brand_name}</Text>
            {brand.is_indian_company && (
              <View style={styles.indianBadge}>
                <Text style={styles.badgeText}>🇮🇳 Indian Brand</Text>
              </View>
            )}
          </View>
        </View>

        {/* India Interest Score */}
        <View style={[styles.section, styles.scoreSection]}>
          <Text style={styles.sectionTitle}>India Interest Score</Text>
          <View style={styles.scoreContainer}>
            <View
              style={[
                styles.scoreCircle,
                { borderColor: getScoreColor(scoreData.score) },
              ]}
            >
              <Text
                style={[
                  styles.scoreText,
                  { color: getScoreColor(scoreData.score) },
                ]}
              >
                {scoreData.score}
              </Text>
              <Text style={styles.scoreMax}>/ 10</Text>
            </View>
          </View>
          <Text style={styles.recommendation}>
            {scoreData.recommendation}
          </Text>
        </View>

        {/* Score Breakdown */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Detailed Breakdown</Text>
          {Object.entries(scoreData.breakdown).map(([key, value]: [string, any]) => (
            <View key={key} style={styles.breakdownItem}>
              <View style={styles.breakdownHeader}>
                <Text style={styles.breakdownTitle}>
                  {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                </Text>
                <Text style={styles.breakdownPoints}>
                  {value.points}/{value.max}
                </Text>
              </View>
              <View style={styles.progressBar}>
                <View
                  style={[
                    styles.progressFill,
                    {
                      width: `${(value.points / value.max) * 100}%`,
                      backgroundColor: getScoreColor((value.points / value.max) * 10),
                    },
                  ]}
                />
              </View>
              <Text style={styles.breakdownStatus}>{value.status}</Text>
            </View>
          ))}
        </View>

        {/* Complete Brand Information */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Complete Information</Text>
          
          <View style={styles.infoRow}>
            <Ionicons name="business-outline" size={20} color="#FF9933" />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Parent Company</Text>
              <Text style={styles.infoValue}>{brand.parent_company}</Text>
            </View>
          </View>

          <View style={styles.infoRow}>
            <Ionicons name="flag-outline" size={20} color="#FF9933" />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Ownership Country</Text>
              <Text style={styles.infoValue}>{brand.ownership_country}</Text>
            </View>
          </View>

          <View style={styles.infoRow}>
            <Ionicons name="location-outline" size={20} color="#FF9933" />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Manufacturing in India</Text>
              <Text style={styles.infoValue}>
                {brand.manufactures_in_india === 'true'
                  ? 'Fully in India'
                  : brand.manufactures_in_india === 'partial'
                  ? 'Partially in India'
                  : 'Not in India'}
              </Text>
            </View>
          </View>

          {brand.manufacturing_states.length > 0 && (
            <View style={styles.infoRow}>
              <Ionicons name="map-outline" size={20} color="#FF9933" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Manufacturing States</Text>
                <Text style={styles.infoValue}>
                  {brand.manufacturing_states.join(', ')}
                </Text>
              </View>
            </View>
          )}

          <View style={styles.infoRow}>
            <Ionicons name="people-outline" size={20} color="#FF9933" />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Employees in India</Text>
              <Text style={styles.infoValue}>
                {brand.employees_in_india_estimate}
              </Text>
            </View>
          </View>

          <View style={styles.infoRow}>
            <Ionicons name="shield-checkmark-outline" size={20} color="#FF9933" />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Data Storage Location</Text>
              <Text style={styles.infoValue}>{brand.data_storage_country}</Text>
            </View>
          </View>

          {brand.security_flags.length > 0 && (
            <View style={styles.infoRow}>
              <Ionicons name="warning-outline" size={20} color="#F44336" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Security Flags</Text>
                <Text style={styles.infoValue}>
                  {brand.security_flags.join(', ')}
                </Text>
              </View>
            </View>
          )}

          {brand.govt_restrictions.length > 0 && (
            <View style={styles.infoRow}>
              <Ionicons name="alert-circle-outline" size={20} color="#FFC107" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Government Restrictions</Text>
                <Text style={styles.infoValue}>
                  {brand.govt_restrictions.join(', ')}
                </Text>
              </View>
            </View>
          )}
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
  },
  section: {
    backgroundColor: '#16213e',
    margin: 16,
    padding: 20,
    borderRadius: 12,
  },
  scoreSection: {
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  brandHeader: {
    alignItems: 'center',
  },
  brandIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#1a1a2e',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  brandName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 12,
  },
  indianBadge: {
    backgroundColor: '#138808',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  badgeText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  scoreContainer: {
    alignItems: 'center',
    marginVertical: 20,
  },
  scoreCircle: {
    width: 160,
    height: 160,
    borderRadius: 80,
    borderWidth: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scoreText: {
    fontSize: 56,
    fontWeight: 'bold',
  },
  scoreMax: {
    fontSize: 18,
    color: '#999',
  },
  recommendation: {
    fontSize: 16,
    color: '#fff',
    textAlign: 'center',
    marginTop: 8,
  },
  breakdownItem: {
    marginBottom: 20,
  },
  breakdownHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  breakdownTitle: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '600',
  },
  breakdownPoints: {
    fontSize: 14,
    color: '#FF9933',
    fontWeight: 'bold',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#1a1a2e',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
  },
  breakdownStatus: {
    fontSize: 12,
    color: '#999',
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  infoContent: {
    flex: 1,
    marginLeft: 12,
  },
  infoLabel: {
    fontSize: 12,
    color: '#999',
    marginBottom: 4,
  },
  infoValue: {
    fontSize: 15,
    color: '#fff',
  },
});
